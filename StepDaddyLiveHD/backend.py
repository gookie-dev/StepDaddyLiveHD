import os
import asyncio
import httpx
from StepDaddyLiveHD.step_daddy import StepDaddy, Channel
from fastapi import Response, status, FastAPI
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from .utils import urlsafe_base64_decode


fastapi_app = FastAPI()
step_daddy = StepDaddy()

# ✅ Build httpx client with optional SOCKS5 support (httpx>=0.28 uses proxy= not proxies=)
SOCKS5 = os.getenv("SOCKS5")
proxy = SOCKS5 if SOCKS5 else None
client = httpx.AsyncClient(http2=True, timeout=None, proxy=proxy)


@fastapi_app.get("/stream/{channel_id}.m3u8")
async def stream(channel_id: str):
    try:
        return Response(
            content=await step_daddy.stream(channel_id),
            media_type="application/vnd.apple.mpegurl",
            headers={f"Content-Disposition": f"attachment; filename={channel_id}.m3u8"},
        )
    except IndexError:
        return JSONResponse(
            content={"error": "Stream not found"},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
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
        return JSONResponse(
            content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@fastapi_app.get("/content/{path}")
async def content(path: str):
    try:
        async def proxy_stream():
            async with client.stream("GET", step_daddy.content_url(path), timeout=60) as response:
                async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
                    yield chunk

        return StreamingResponse(
            proxy_stream(), media_type="application/octet-stream"
        )
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def update_channels():
    while True:
        try:
            await step_daddy.load_channels()
            await asyncio.sleep(300)
        except asyncio.CancelledError:
            continue


def get_channels():
    return step_daddy.channels


def get_channel(channel_id) -> Channel | None:
    if not channel_id or channel_id == "":
        return None
    return next(
        (channel for channel in step_daddy.channels if channel.id == channel_id), None
    )


@fastapi_app.get("/playlist.m3u8")
def playlist():
    return Response(
        content=step_daddy.playlist(),
        media_type="application/vnd.apple.mpegurl",
        headers={"Content-Disposition": "attachment; filename=playlist.m3u8"},
    )


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
        response = await client.get(
            url,
            headers={
                "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0"
            },
        )
        if response.status_code == 200:
            with open(f"./logo-cache/{file}", "wb") as f:
                f.write(response.content)
            return FileResponse(f"./logo-cache/{file}")
        else:
            return JSONResponse(
                content={"error": "Logo not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except httpx.ConnectTimeout:
        return JSONResponse(
            content={"error": "Request timed out"},
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ✅ Proxy Test Endpoint
@fastapi_app.get("/api/whatsmyip")
async def whats_my_ip():
    """Check public IP and confirm proxy usage."""
    proxy_cfg = SOCKS5 if SOCKS5 else None
    async with httpx.AsyncClient(proxy=proxy_cfg) as test_client:
        r = await test_client.get("https://api.my-ip.io/ip.json", timeout=10.0)
        return JSONResponse(
            {
                "reported_ip": r.json(),
                "using_proxy": bool(SOCKS5),
                "proxy_env": SOCKS5 or "None",
            }
        )
