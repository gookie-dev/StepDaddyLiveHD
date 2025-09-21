import os
import asyncio
import httpx
from StepDaddyLiveHD.step_daddy import StepDaddy, Channel, EpgProgram
from fastapi import Response, status, FastAPI
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from .epg import generate_epg
from .utils import urlsafe_base64_decode


fastapi_app = FastAPI()
step_daddy = StepDaddy()
client = httpx.AsyncClient(http2=True, timeout=None, verify=False)
epg_ready = asyncio.Event()


@fastapi_app.get("/stream/{channel_id}.m3u8")
async def stream(channel_id: str):
    try:
        return Response(
            content=await step_daddy.stream(channel_id),
            media_type="application/vnd.apple.mpegurl",
            headers={f"Content-Disposition": f"attachment; filename={channel_id}.m3u8"}
        )
    except IndexError:
        return JSONResponse(content={"error": "Stream not found"}, status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@fastapi_app.get("/key/{url}/{host}")
async def key(url: str, host: str):
    try:
        return Response(
            content=await step_daddy.key(url, host),
            media_type="application/octet-stream",
            headers={"Content-Disposition": "attachment; filename=key"}
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@fastapi_app.get("/content/{path}")
async def content(path: str):
    try:
        async def proxy_stream():
            async with client.stream("GET", step_daddy.content_url(path), timeout=60) as response:
                async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
                    yield chunk
        return StreamingResponse(proxy_stream(), media_type="application/octet-stream")
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def update_channels():
    while True:
        try:
            await step_daddy.load_channels()
            await asyncio.sleep(300)
        except asyncio.CancelledError:
            continue


async def update_epg():
    while True:
        try:
            await generate_epg(step_daddy)
            if not epg_ready.is_set():
                epg_ready.set()
            await asyncio.sleep(60 * 60 * 24)  # Update once a day
        except asyncio.CancelledError:
            continue


def get_channels():
    return step_daddy.channels


def get_channel(channel_id) -> Channel | None:
    if not channel_id or channel_id == "":
        return None
    return next((channel for channel in step_daddy.channels if channel.id == channel_id), None)


def get_now_playing_map():
    """
    Ritorna una mappa {channel_id: {title, desc, start_dt, stop_dt}} per i canali con tvg_id valido.
    Usa i dati già presenti in step_daddy.epg_data.
    """
    result = {}
    for ch in step_daddy.channels:
        if not getattr(ch, "tvg_id", None):
            continue
        programs = step_daddy.get_epg_for_channel(ch.tvg_id)
        if programs:
            p = programs[0]
            result[ch.id] = {
                "title": p.title,
                "desc": p.desc,
                "start_dt": p.start_dt.isoformat(),
                "stop_dt": p.stop_dt.isoformat(),
            }
    return result






@fastapi_app.get("/playlist.m3u8")
def playlist():
    return Response(content=step_daddy.playlist(), media_type="application/vnd.apple.mpegurl", headers={"Content-Disposition": "attachment; filename=playlist.m3u8"})


@fastapi_app.get("/epg.xml")
def epg():
    return FileResponse("epg.xml", media_type="application/xml", headers={"Content-Disposition": "attachment; filename=epg.xml"})


@fastapi_app.get("/epg/channel/{channel_id}")
async def epg_for_channel(channel_id: str):
    await epg_ready.wait()  # Attendi che l'EPG sia pronto
    channel = get_channel(channel_id)
    if not channel or not channel.tvg_id:
        return []
    
    programs = step_daddy.get_epg_for_channel(channel.tvg_id)
    # Convertiamo manualmente i dati in un formato JSON-safe
    epg_list = [
        {
            "start": p.start,
            "stop": p.stop,
            "title": p.title,
            "desc": p.desc,
            "start_dt": p.start_dt.isoformat(),
            "stop_dt": p.stop_dt.isoformat(),
        }
        for p in programs
    ]
    return epg_list




async def get_schedule():
    return await step_daddy.schedule()


@fastapi_app.get("/logo/{logo}")
async def logo(logo: str):
    url = urlsafe_base64_decode(logo)
    file = url.split("/")[-1]
    if not os.path.exists("./logo-cache"):
        os.makedirs("./logo-cache")
    if os.path.exists(f"./logo-cache/{file}"):
        return FileResponse(f"./logo-cache/{file}")
    try:
        response = await client.get(url, headers={"user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0"})
        if response.status_code == 200:
            with open(f"./logo-cache/{file}", "wb") as f:
                f.write(response.content)
            return FileResponse(f"./logo-cache/{file}")
        else:
            return JSONResponse(content={"error": "Logo not found"}, status_code=status.HTTP_404_NOT_FOUND)
    except httpx.ConnectTimeout:
        return JSONResponse(content={"error": "Request timed out"}, status_code=status.HTTP_504_GATEWAY_TIMEOUT)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
