import json
import re
import reflex as rx
from urllib.parse import quote, urlparse
from curl_cffi import AsyncSession
from typing import List, Optional
from .utils import encrypt, decrypt, urlsafe_base64
from rxconfig import config


class Channel(rx.Base):
    id: str
    name: str
    tags: List[str]
    logo: str
    country: Optional[str] = None
    country_flag: Optional[str] = None


class StepDaddy:
    def __init__(self):
        socks5 = config.socks5
        if socks5 != "":
            self._session = AsyncSession(proxy="socks5://" + socks5)
        else:
            self._session = AsyncSession()
        self._base_url = "https://daddylive.dad"
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

    def _get_country_from_tags(self, tags: List[str]) -> tuple[Optional[str], Optional[str]]:
        for tag in tags:
            if len(tag) == 2 and all(c in '🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿' for c in tag):
                country_map = {
                    '🇮🇹': 'Italy',
                    '🇬🇧': 'United Kingdom',
                    '🇺🇸': 'United States',
                    '🇪🇸': 'Spain',
                    '🇫🇷': 'France',
                    '🇩🇪': 'Germany',
                    # Add more country mappings as needed
                }
                return country_map.get(tag, 'Other'), tag
        return None, None

    async def load_channels(self):
        channels = []
        try:
            response = await self._session.get(f"{self._base_url}/24-7-channels.php", headers=self._headers())
            channels_block = re.compile("<center><h1(.+?)tab-2", re.MULTILINE | re.DOTALL).findall(str(response.text))
            channels_data = re.compile("href=\"(.*)\" target(.*)<strong>(.*)</strong>").findall(channels_block[0])
            for channel_data in channels_data:
                channels.append(self._get_channel(channel_data))
        finally:
            self.channels = sorted(channels, key=lambda channel: (channel.country or 'ZZZ', channel.name.startswith("18"), channel.name))

    def _get_channel(self, channel_data) -> Channel:
        channel_id = channel_data[0].split('-')[1].replace('.php', '')
        channel_name = channel_data[2]
        if channel_id == "666":
            channel_name = "Nick Music"
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
        tags = meta.get("tags", [])
        country, country_flag = self._get_country_from_tags(tags)
        return Channel(
            id=channel_id,
            name=channel_name,
            tags=tags,
            logo=logo,
            country=country,
            country_flag=country_flag
        )

    async def stream(self, channel_id: str):
        url = f"{self._base_url}/stream/stream-{channel_id}.php"
        if len(channel_id) > 3:
            url = f"{self._base_url}/stream/bet.php?id=bet{channel_id}"
        response = await self._session.post(url, headers=self._headers())
        source_url = re.compile("iframe src=\"(.*)\" width").findall(response.text)[0]
        source_response = await self._session.post(source_url, headers=self._headers(url))

        channel_key = re.compile(r"var\s+channelKey\s*=\s*\"(.*?)\";").findall(source_response.text)[-1]
        auth_ts = re.compile(r"var\s+authTs\s*=\s*\"(.*?)\";").findall(source_response.text)[-1]
        auth_rnd = re.compile(r"var\s+authRnd\s*=\s*\"(.*?)\";").findall(source_response.text)[-1]
        auth_sig = re.compile(r"var\s+authSig\s*=\s*\"(.*?)\";").findall(source_response.text)[-1]
        auth_request_url = f"https://top2new.newkso.ru/auth.php?channel_id={channel_key}&ts={auth_ts}&rnd={auth_rnd}&sig={auth_sig}"
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
        data = "#EXTM3U\n"
        current_country = None
        for channel in self.channels:
            if channel.country and channel.country != current_country:
                current_country = channel.country
                data += f"\n#EXTGRP:{current_country}\n"
            
            tvg_tags = []
            if channel.logo:
                tvg_tags.append(f'tvg-logo="{channel.logo}"')
            if channel.country:
                tvg_tags.append(f'group-title="{channel.country}"')
            if channel.country_flag:
                channel_name = f"{channel.country_flag} {channel.name}"
            else:
                channel_name = channel.name
            
            tvg_string = " ".join(tvg_tags)
            data += f"#EXTINF:-1 {tvg_string},{channel_name}\n"
            data += f"{config.api_url}/stream/{channel.id}.m3u8\n"
        return data

    async def schedule(self):
        response = await self._session.get(f"{self._base_url}/schedule/schedule-generated.php", headers=self._headers())
        return response.json()