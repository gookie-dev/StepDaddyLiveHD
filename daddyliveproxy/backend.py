import asyncio
import json
import re
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse
from xml.etree.ElementTree import Element, SubElement, tostring
from zoneinfo import ZoneInfo

import httpx
from dateutil import parser
from fastapi import FastAPI, Query, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from daddyliveproxy.logging import configure_logging, get_log_file, get_logger
from daddyliveproxy.step_daddy import Channel, StepDaddy

from .utils import urlsafe_base64_decode

CHANNEL_FILE = Path("channels.json")

configure_logging()  # Once at import time

logger = get_logger("backend")

fastapi_app = FastAPI()


@fastapi_app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Log 404 errors and return a standard response."""
    logger.warning("404 Not Found: %s", request.url.path)
    return JSONResponse({"detail": "Not Found"}, status_code=status.HTTP_404_NOT_FOUND)


step_daddy = StepDaddy()
client = httpx.AsyncClient(
    http2=True,
    timeout=httpx.Timeout(15.0, read=60.0),
    follow_redirects=True,
)


@fastapi_app.on_event("startup")
async def _startup() -> None:
    """Ensure we have an initial channel list on boot."""
    if not step_daddy.channels:
        try:
            await step_daddy.load_channels()
        except Exception:
            logger.exception("Initial channel load failed")


@fastapi_app.on_event("shutdown")
async def _shutdown() -> None:
    """Close shared HTTP clients cleanly."""
    await client.aclose()
    await step_daddy.aclose()


def get_selected_channel_ids() -> set[str]:
    """Return the set of enabled channel IDs."""
    if CHANNEL_FILE.exists():
        try:
            raw = json.loads(CHANNEL_FILE.read_text())
            if isinstance(raw, list):
                return {str(ch) for ch in raw}
            logger.warning(
                "Channel selection file contained unexpected data: %s", type(raw)
            )
        except json.JSONDecodeError:
            logger.warning(
                "Channel selection file is not valid JSON; using all channels"
            )
        except OSError as exc:
            logger.warning("Unable to read channel selection file: %s", exc)
    return {ch.id for ch in step_daddy.channels}


def set_selected_channel_ids(ids: list[str]) -> None:
    """Persist the selected channel IDs."""
    cleaned = sorted({str(cid) for cid in ids if cid})
    try:
        CHANNEL_FILE.write_text(json.dumps(cleaned))
    except OSError:
        logger.exception("Failed to persist channel selection")
        raise


@fastapi_app.get("/stream/{channel_id}.m3u8")
async def stream(channel_id: str):
    if not channel_id:
        return JSONResponse(
            content={"error": "Channel id is required"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        playlist_body = await step_daddy.stream(channel_id)
        return Response(
            content=playlist_body,
            media_type="application/vnd.apple.mpegurl",
            headers={"Content-Disposition": f"attachment; filename={channel_id}.m3u8"},
        )
    except ValueError as exc:
        logger.warning("Stream not available for %s: %s", channel_id, exc)
        return JSONResponse(
            content={"error": "Stream not found"},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.exception("Stream error for %s", channel_id)
        return JSONResponse(
            content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@fastapi_app.get("/key/{url}/{host}")
async def key(url: str, host: str):
    try:
        return Response(
            content=await step_daddy.key(url, host),
            media_type="application/octet-stream",
            headers={"Content-Disposition": "attachment; filename=key"},
        )
    except Exception as e:
        logger.exception("Key request failed")
        return JSONResponse(
            content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@fastapi_app.get("/content/{path:path}")
async def content(path: str):
    try:

        async def proxy_stream():
            url = step_daddy.content_url(path)
            async with client.stream("GET", url, timeout=60) as response:
                async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
                    yield chunk

        return StreamingResponse(proxy_stream(), media_type="application/octet-stream")
    except Exception as e:
        return JSONResponse(
            {"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def update_channels():
    """Periodically refresh channels (no guide persistence anymore)."""
    try:
        await step_daddy.load_channels()
        logger.info("Channels refreshed on startup")
    except Exception:
        logger.exception("Failed to update channels on startup")

    while True:
        try:
            await step_daddy.load_channels()
            logger.info("Channels refreshed")
        except asyncio.CancelledError:
            logger.info("Channel refresh task cancelled")
            break
        except Exception:
            logger.exception("Failed to update channels")
            await asyncio.sleep(60)
            continue
        await asyncio.sleep(300)


def get_channels() -> list[Channel]:
    """Return a copy of the loaded channels."""
    return list(step_daddy.channels)


def get_enabled_channels() -> list[Channel]:
    """Return only the channels that are currently enabled."""
    selected = get_selected_channel_ids()
    return [ch for ch in step_daddy.channels if ch.id in selected]


def get_channel(channel_id: str) -> Channel | None:
    """Return the channel with the given ID if it exists."""
    if not channel_id:
        return None
    return next(
        (channel for channel in step_daddy.channels if channel.id == channel_id), None
    )


@fastapi_app.get("/playlist.m3u8")
def playlist(
    download: bool = Query(False),
    view: bool = Query(False),
):
    selected = get_selected_channel_ids()
    channels = [ch for ch in step_daddy.channels if ch.id in selected]

    headers = {"Cache-Control": "no-store"}
    media_type = "application/vnd.apple.mpegurl"  # default HLS type

    if download:
        headers["Content-Disposition"] = "attachment; filename=playlist.m3u8"
    elif view:
        media_type = "text/plain; charset=utf-8"  # render as text in browser

    return Response(
        content=step_daddy.playlist(channels),
        media_type=media_type,
        headers=headers,
    )


async def get_schedule():
    """Fetch and filter schedule to selected channels."""
    try:
        schedule = await step_daddy.schedule()
    except Exception:
        logger.exception("Failed to fetch upstream schedule")
        return {}
    selected = get_selected_channel_ids()

    # Build lookup maps for resolving channel name/id mismatches.
    id_to_name = {ch.id: ch.name for ch in step_daddy.channels}

    def norm(name: str) -> str:
        """Return a simplified version of a channel name."""
        return re.sub(r"\W+", "", name or "").lower()

    name_to_id: dict[str, str] = {}
    for ch in step_daddy.channels:
        key = norm(ch.name)
        # Prefer selected channels when multiple share the same name.
        if key not in name_to_id or ch.id in selected:
            name_to_id[key] = ch.id

    def filter_channels(data):
        def resolve(chan: dict):
            cid = str(chan.get("channel_id", ""))
            name = chan.get("channel_name", "")
            mapped = name_to_id.get(norm(name))
            if id_to_name.get(cid) != name:
                if mapped:
                    cid = mapped
                else:
                    return None
            if cid in selected:
                chan = chan.copy()
                chan["channel_id"] = cid
                return chan
            return None

        if isinstance(data, list):
            return [c for c in (resolve(x) for x in data) if c]
        if isinstance(data, dict):
            return {k: v for k, v in ((k, resolve(v)) for k, v in data.items()) if v}
        return []

    filtered = {}
    for day, categories in schedule.items():
        for category, events in categories.items():
            new_events = []
            for event in events:
                ch1 = filter_channels(event.get("channels"))
                ch2 = filter_channels(event.get("channels2"))
                if not ch1 and not ch2:
                    continue
                e = event.copy()
                if ch1:
                    e["channels"] = ch1
                else:
                    e.pop("channels", None)
                if ch2:
                    e["channels2"] = ch2
                else:
                    e.pop("channels2", None)
                new_events.append(e)
            if new_events:
                filtered.setdefault(day, {})[category] = new_events
    return filtered


async def build_guide() -> bytes:
    """
    Build XMLTV guide **in memory** and return bytes.
    No file writes, no persistence.
    """
    schedule = await get_schedule()
    selected = get_selected_channel_ids()

    root = Element("tv", attrib={"generator-info-name": "daddyliveproxy"})
    added_channels = set()

    # Known channels with logos
    for ch in step_daddy.channels:
        if ch.id not in selected:
            continue
        channel_elem = SubElement(root, "channel", id=ch.id)
        SubElement(channel_elem, "display-name").text = ch.name
        if ch.logo:
            SubElement(channel_elem, "icon", src=ch.logo)
        added_channels.add(ch.id)

    def ensure_channel(channel: dict):
        cid = channel.get("channel_id")
        if cid and cid in selected and cid not in added_channels:
            elem = SubElement(root, "channel", id=cid)
            SubElement(elem, "display-name").text = channel.get("channel_name", cid)
            added_channels.add(cid)

    def iter_channels(data):
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return list(data.values())
        return []

    utc = ZoneInfo("UTC")

    for day, categories in schedule.items():
        date = parser.parse(day.split(" - ")[0], dayfirst=True)
        for category, events in categories.items():
            for event in events:
                time_str = event.get("time")
                if not time_str:
                    logger.debug(
                        "Skipping schedule entry without a start time: %s", event
                    )
                    continue
                try:
                    hour, minute = map(int, time_str.split(":"))
                except ValueError:
                    logger.debug(
                        "Invalid schedule time '%s' for event %s", time_str, event
                    )
                    continue
                start = date.replace(hour=hour, minute=minute, tzinfo=utc)
                stop = start + timedelta(hours=1)
                for channel in iter_channels(event.get("channels")) + iter_channels(
                    event.get("channels2")
                ):
                    ensure_channel(channel)
                    programme = SubElement(
                        root,
                        "programme",
                        start=start.strftime("%Y%m%d%H%M%S +0000"),
                        stop=stop.strftime("%Y%m%d%H%M%S +0000"),
                        channel=channel.get("channel_id"),
                    )
                    SubElement(programme, "title", lang="en").text = (
                        event.get("event") or "Unknown"
                    )
                    SubElement(programme, "category").text = category

    return tostring(root, encoding="utf-8", xml_declaration=True)


@fastapi_app.get("/guide.xml")
async def guide(download: bool = Query(False)):
    xml_bytes = await build_guide()
    headers = {"Cache-Control": "no-store"}
    if download:
        headers["Content-Disposition"] = "attachment; filename=guide.xml"
    return Response(
        content=xml_bytes,
        media_type="application/xml; charset=utf-8",
        headers=headers,
    )


async def refresh_all():
    """Manually refresh channels (guide is served live, so no persistence)."""
    logger.info("Manual refresh requested")
    await step_daddy.load_channels()
    logger.info("Manual refresh complete")


@fastapi_app.post("/refresh")
async def refresh():
    try:
        await refresh_all()
        return JSONResponse({"status": "ok"})
    except Exception as e:
        logger.exception("Manual refresh failed")
        return JSONResponse(
            {"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@fastapi_app.get("/logo/{logo}")
async def logo(logo: str):
    try:
        url = urlsafe_base64_decode(logo)
    except Exception as exc:
        logger.warning("Invalid logo token provided: %s", exc)
        return JSONResponse(
            content={"error": "Invalid logo reference"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    filename = Path(urlparse(url).path).name or "logo"
    logo_dir = Path("logo-cache")
    try:
        logo_dir.mkdir(exist_ok=True)
    except OSError as exc:
        logger.exception("Failed to create logo cache directory")
        return JSONResponse(
            content={"error": "Internal server error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    cache_path = logo_dir / filename
    if cache_path.exists():
        return FileResponse(cache_path)

    try:
        response = await client.get(
            url,
            headers={
                "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0"
            },
        )
    except httpx.ConnectTimeout:
        return JSONResponse(
            content={"error": "Request timed out"},
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )
    except httpx.RequestError:
        logger.exception("Logo download failed for %s", url)
        return JSONResponse(
            content={"error": "Failed to download logo"},
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    if response.status_code != status.HTTP_200_OK:
        return JSONResponse(
            content={"error": "Logo not found"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    try:
        cache_path.write_bytes(response.content)
    except OSError:
        logger.exception("Failed to cache logo to disk")
        media_type = response.headers.get("content-type", "image/png")
        return Response(content=response.content, media_type=media_type)

    return FileResponse(cache_path)


@fastapi_app.get("/logs")
def logs():
    """Return the application log file."""
    log_file = get_log_file()
    log_file.parent.mkdir(parents=True, exist_ok=True)
    if not log_file.exists():
        log_file.touch()
    return FileResponse(log_file)
