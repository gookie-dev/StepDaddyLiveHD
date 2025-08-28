import json
import re
import reflex as rx
from urllib.parse import quote, urlparse
from curl_cffi import AsyncSession
from typing import List
from .utils import encrypt, decrypt, urlsafe_base64, decode_bundle
from rxconfig import config


class Channel(rx.Base):
    id: str
    name: str
    tags: List[str]
    logo: str


class StepDaddy:
    def __init__(self):
        socks5 = config.socks5
        if socks5 != "":
            # Use SOCKS5 env var directly (it already includes the socks5:// prefix)
            self._session = AsyncSession(proxy=socks5)
        else:
            self._session = AsyncSession()
        self._base_url = "https://thedaddy.top"
        self.channels = []
        with open("StepDaddyLiveHD/meta.json", "r") as f:
            self._meta = json.load(f)

    def _headers(self, referer: str = None, origin: str = None):
        if referer is None:
            referer = self._base_url
        headers = {
            "Referer": referer,
            "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0",
        }
        if origin:
            headers["Origin"] = origin
        return headers

    async def load_channels(self):
        channels = []
        try:
            response = await self._session.get(
                f"{self._base_url}/24-7-channels.php", headers=self._headers()
            )
            # Updated regex to match new HTML format:
            # <div class="grid-item"><a href="/stream/stream-492.php" target="_blank" rel="noopener"><span style="color: #000000;"><strong>Channel Name</strong></span></a></div>
            channels_data = re.compile(
                r'href="(/stream/stream-\d+\.php)".*?<strong>(.*?)</strong>',
                re.DOTALL
            ).findall(response.text)
            
            for channel_data in channels_data:
                channels.append(self._get_channel(channel_data))
        finally:
            self.channels = sorted(
                channels,
                key=lambda channel: (channel.name.startswith("18"), channel.name),
            )

    def _get_channel(self, channel_data) -> Channel:
        # channel_data[0] is now "/stream/stream-492.php"
        # Extract the ID from the path
        channel_id = re.search(r'stream-(\d+)\.php', channel_data[0]).group(1)
        channel_name = channel_data[1]
        
        # Apply name corrections
        if channel_id == "666":
            channel_name = "Nick Music"
        if channel_id == "609":
            channel_name = "Yas TV UAE"
        if channel_name == "#0 Spain":
            channel_name = "Movistar Plus+"
        elif channel_name == "#Vamos Spain":
            channel_name = "Vamos Spain"
            
        clean_channel_name = re.sub(r"\s*\(.*?\)", "", channel_name)
        meta = self._meta.get(clean_channel_name, {})
        logo = meta.get("logo", "/missing.png")
        if logo.startswith("http"):
            logo = f"{config.api_url}/logo/{urlsafe_base64(logo)}"
        return Channel(
            id=channel_id,
            name=channel_name,
            tags=meta.get("tags", []),
            logo=logo,
        )

    # Not generic
    async def stream(self, channel_id: str):
        key = "CHANNEL_KEY"

        prefixes = ["stream", "cast", "watch"]
        for prefix in prefixes:
            url = f"{self._base_url}/{prefix}/stream-{channel_id}.php"
            if len(channel_id) > 3:
                url = f"{self._base_url}/{prefix}/bet.php?id=bet{channel_id}"
            response = await self._session.post(url, headers=self._headers())
            matches = re.compile("iframe src=\"(.*)\" width").findall(response.text)
            if matches:
                source_url = matches[0]
                source_response = await self._session.post(
                    source_url, headers=self._headers(url)
                )
                if key in source_response.text:
                    break
        else:
            raise ValueError("Failed to find source URL for channel")

        channel_key = re.compile(
            rf"const\s+{re.escape(key)}\s*=\s*\"(.*?)\";"
        ).findall(source_response.text)[-1]
        bundle = re.compile(r"const\s+XJZ\s*=\s*\"(.*?)\";").findall(
            source_response.text
        )[-1]
        data = decode_bundle(bundle)
        auth_ts = data.get("b_ts", "")
        auth_sig = data.get("b_sig", "")
        auth_rnd = data.get("b_rnd", "")
        auth_url = data.get("b_host", "")
        auth_request_url = (
            f"{auth_url}auth.php?channel_id={channel_key}"
            f"&ts={auth_ts}&rnd={auth_rnd}&sig={auth_sig}"
        )
        auth_response = await self._session.get(
            auth_request_url, headers=self._headers(source_url)
        )
        if auth_response.status_code != 200:
            raise ValueError("Failed to get auth response")
        key_url = urlparse(source_url)
        key_url = (
            f"{key_url.scheme}://{key_url.netloc}/server_lookup.php?channel_id={channel_key}"
        )
        key_response = await self._session.get(
            key_url, headers=self._headers(source_url)
        )
        server_key = key_response.json().get("server_key")
        if not server_key:
            raise ValueError("No server key found in response")
        if server_key == "top1/cdn":
            server_url = (
                f"https://top1.newkso.ru/top1/cdn/{channel_key}/mono.m3u8"
            )
        else:
            server_url = (
                f"https://{server_key}new.newkso.ru/{server_key}/{channel_key}/mono.m3u8"
            )
        m3u8 = await self._session.get(
            server_url, headers=self._headers(quote(str(source_url)))
        )
        m3u8_data = ""
        for line in m3u8.text.split("\n"):
            if line.startswith("#EXT-X-KEY:"):
                original_url = re.search(r'URI="(.*?)"', line).group(1)
                line = line.replace(
                    original_url,
                    f"{config.api_url}/key/{encrypt(original_url)}/{encrypt(urlparse(source_url).netloc)}",
                )
            elif line.startswith("http") and config.proxy_content:
                line = f"{config.api_url}/content/{encrypt(line)}"
            m3u8_data += line + "\n"
        return m3u8_data

    async def key(self, url: str, host: str):
        url = decrypt(url)
        host = decrypt(host)
        response = await self._session.get(
            url, headers=self._headers(f"{host}/", host), timeout=60
        )
        if response.status_code != 200:
            raise Exception("Failed to get key")
        return response.content

    @staticmethod
    def content_url(path: str):
        return decrypt(path)

    def playlist(self):
        data = "#EXTM3U\n"
        for channel in self.channels:
            entry = (
                f' tvg-logo="{channel.logo}",{channel.name}'
                if channel.logo
                else f",{channel.name}"
            )
            data += (
                f"#EXTINF:-1{entry}\n{config.api_url}/stream/{channel.id}.m3u8\n"
            )
        return data

    async def schedule(self):
        response = await self._session.get(
            f"{self._base_url}/schedule/schedule-generated.php",
            headers=self._headers(),
        )
        return response.json()
