import json
import re
import reflex as rx
from pydantic import model_serializer
from urllib.parse import quote, urlparse
from datetime import datetime
from zoneinfo import ZoneInfo
from curl_cffi import AsyncSession
from typing import List, Dict
from .utils import encrypt, decrypt, urlsafe_base64, decode_bundle
from rxconfig import config


class Channel(rx.Base):
    id: str
    name: str
    tvg_id: str
    tags: List[str]
    logo: str


class EpgProgram(rx.Base):
    start: str
    stop: str
    title: str
    desc: str | None = None
    start_dt: datetime
    stop_dt: datetime


class StepDaddy:
    def __init__(self):
        socks5 = config.socks5
        if socks5 != "":
            self._session = AsyncSession(proxy="socks5://" + socks5, verify=False)
        else:
            self._session = AsyncSession(verify=False)
        self._base_url = "https://dlhd.dad/"
        self.epg_data: Dict[str, List[EpgProgram]] = {}
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
            response = await self._session.get(f"{self._base_url}/24-7-channels.php", headers=self._headers())
            response.raise_for_status()  # Assicura che la richiesta sia andata a buon fine
            channels_html = re.findall(r'<a class="card".*?</a>', response.text, re.DOTALL)
            for channel_html in channels_html:
                if channel := self._parse_channel_from_html(channel_html):
                    channels.append(channel)
        finally:
            if channels:
                self.channels = sorted(channels, key=lambda channel: (channel.name.startswith("18"), channel.name))

    def _get_channel(self, channel_data) -> Channel:
        id_match = re.search(r'\d+', channel_data[0])
        if not id_match:
            raise ValueError(f"Could not extract channel ID from {channel_data[0]}")
        channel_id = id_match.group(0)
        channel_name = channel_data[2]
        if channel_id == "666":
            channel_name = "Nick Music"
        if channel_id == "853":
            channel_name = "Canale 5 Italy"
        if channel_id == "877":
            channel_name = "DAZN 1 Italy"
        if channel_id == "609":
            channel_name = "Yas TV UAE"
        if channel_data[2] == "#0 Spain":
            channel_name = "Movistar Plus+"
        elif channel_data[2] == "#Vamos Spain":
            channel_name = "Vamos Spain"
        clean_channel_name = re.sub(r"\s*\(.*?\)", "", channel_name)
        meta = self._meta.get(clean_channel_name, {})
        logo = meta.get("logo", "/missing.png")
        if logo.startswith("http"):
            logo = f"{config.api_url}/logo/{urlsafe_base64(logo)}"
        return Channel(id=channel_id, name=channel_name, tvg_id=meta.get("tvg_id", ""), tags=meta.get("tags", []), logo=logo)

    def _parse_channel_from_html(self, html_block: str) -> Channel | None:
        href_match = re.search(r'href="/watch\.php\?id=(\d+)"', html_block)
        name_match = re.search(r'<div class="card__title">(.*?)</div>', html_block)

        if not href_match or not name_match:
            return None

        channel_id = href_match.group(1)
        return self._get_channel((f"watch.php?id={channel_id}", "", name_match.group(1)))

    # Not generic
    async def stream(self, channel_id: str):
        key = "CHANNEL_KEY"

        prefixes = ["stream", "cast", "watch", "plus", "casting", "player"]
        for prefix in prefixes:
            url = f"{self._base_url}/{prefix}/stream-{channel_id}.php"
            if len(channel_id) > 3:
                url = f"{self._base_url}/{prefix}/bet.php?id=bet{channel_id}"
            response = await self._session.post(url, headers=self._headers())
            matches = re.compile("iframe src=\"(.*)\" width").findall(response.text)
            if matches:
                source_url = matches[0]
                source_response = await self._session.post(source_url, headers=self._headers(url))
                if key in source_response.text:
                    break
        else:
            raise ValueError("Failed to find source URL for channel")

        channel_key = re.compile(rf"const\s+{re.escape(key)}\s*=\s*\"(.*?)\";").findall(source_response.text)[-1]
        bundle = re.compile(r"const\s+XJZ\s*=\s*\"(.*?)\";").findall(source_response.text)[-1]
        data = decode_bundle(bundle)
        auth_ts = data.get("b_ts", "")
        auth_sig = data.get("b_sig", "")
        auth_rnd = data.get("b_rnd", "")
        auth_url = data.get("b_host", "")
        auth_request_url = f"{auth_url}auth.php?channel_id={channel_key}&ts={auth_ts}&rnd={auth_rnd}&sig={auth_sig}"
        auth_response = await self._session.get(auth_request_url, headers=self._headers(source_url))
        if auth_response.status_code != 200:
            raise ValueError("Failed to get auth response")
        key_url = urlparse(source_url)
        key_url = f"{key_url.scheme}://{key_url.netloc}/server_lookup.php?channel_id={channel_key}"
        key_response = await self._session.get(key_url, headers=self._headers(source_url))
        server_key = key_response.json().get("server_key")
        if not server_key:
            raise ValueError("No server key found in response")
        if server_key == "top1/cdn":
            server_url = f"https://top1.newkso.ru/top1/cdn/{channel_key}/mono.m3u8"
        else:
            server_url = f"https://{server_key}new.newkso.ru/{server_key}/{channel_key}/mono.m3u8"
        m3u8 = await self._session.get(server_url, headers=self._headers(quote(str(source_url))))
        m3u8_data = ""
        for line in m3u8.text.split("\n"):
            if line.startswith("#EXT-X-KEY:"):
                original_url = re.search(r'URI="(.*?)"', line).group(1)
                line = line.replace(original_url, f"{config.api_url}/key/{encrypt(original_url)}/{encrypt(urlparse(source_url).netloc)}")
            elif line.startswith("http") and config.proxy_content:
                line = f"{config.api_url}/content/{encrypt(line)}"
            m3u8_data += line + "\n"
        return m3u8_data

    async def key(self, url: str, host: str):
        url = decrypt(url)
        host = decrypt(host)
        response = await self._session.get(url, headers=self._headers(f"{host}/", host), timeout=60)
        if response.status_code != 200:
            raise Exception(f"Failed to get key")
        return response.content

    @staticmethod
    def content_url(path: str):
        return decrypt(path)

    def playlist(self):
        epg_url = f"{config.api_url}/epg.xml"
        data = f'#EXTM3U url-tvg="{epg_url}"\n'
        for channel in self.channels:
            attributes = f'tvg-id="{channel.tvg_id}" tvg-logo="{channel.logo}"'
            data += f'#EXTINF:-1 {attributes},{channel.name}\n{config.api_url}/stream/{channel.id}.m3u8\n'
        return data

    def get_epg_for_channel(self, tvg_id: str) -> List[EpgProgram]:
        now = datetime.now(ZoneInfo("UTC"))
        programs = self.epg_data.get(tvg_id, [])
        # Restituisce i programmi non ancora terminati, ordinati per orario di inizio
        return sorted(
            [p for p in programs if p.stop_dt > now],
            key=lambda p: p.start_dt
        )

    async def schedule(self):
        response = await self._session.get(f"{self._base_url}/schedule/schedule-generated.php", headers=self._headers())
        return response.json()
