import asyncio
import gzip
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from dateutil import parser

import httpx

from .step_daddy import StepDaddy, EpgProgram


EPG_URLS = [
    "http://m3u4u.com/xml/5g28nezee8sv3dk7yzpe",
    "https://epgshare01.online/epgshare01/epg_ripper_AR1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_AU1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_BEIN1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_BG1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_BR1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_CA1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_CL1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_CO1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_CR1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_CY1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_DK1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_ES1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_FANDUEL1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_FR1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_GR1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_HR1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_IL1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_IN4.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_IT1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_MX1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_MY1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_NL1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_NZ1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_PK1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_PL1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_RO1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_RO2.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_SA1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_SE1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_TR1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS2.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_UY1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_ZA1.xml.gz",
]


async def fetch_and_parse_xml(client: httpx.AsyncClient, url: str) -> ET.Element | None:
    try:
        response = await client.get(url, timeout=30)
        response.raise_for_status()
        content = await response.aread()
        if url.endswith('.gz'):
            content = gzip.decompress(content)
        return ET.fromstring(content)
    except (httpx.HTTPError, ET.ParseError, gzip.BadGzipFile) as e:
        print(f"Failed to process EPG from {url}: {e}")
        return None


async def generate_epg(step_daddy: StepDaddy):
    print("Generating EPG...")
    root = ET.Element('tv')
    parsed_epg = defaultdict(list)
    seen_channels = set()
    seen_programmes = set()

    async with httpx.AsyncClient(http2=True, timeout=None, verify=False) as client:
        tasks = [fetch_and_parse_xml(client, url) for url in EPG_URLS]
        for epg_data in await asyncio.gather(*tasks):
            if epg_data is None:
                continue

            for channel in epg_data.findall('channel'):
                cid = channel.get('id')
                if cid and cid not in seen_channels:
                    root.append(channel)
                    seen_channels.add(cid)

            for programme in epg_data.findall('programme'):
                start_str = programme.get("start")
                stop_str = programme.get("stop")
                chan = programme.get('channel')
                if not start_str or not stop_str or not chan:
                    continue
                prog_key = (chan, start_str, stop_str)
                if prog_key in seen_programmes:
                    continue
                title_elem = programme.find("title")
                desc_elem = programme.find("desc")
                parsed_epg[chan].append(EpgProgram(
                    start=start_str,
                    stop=stop_str,
                    title=title_elem.text if title_elem is not None else "No Title",
                    desc=desc_elem.text if desc_elem is not None else None,
                    start_dt=parser.parse(start_str),
                    stop_dt=parser.parse(stop_str),
                ))
                root.append(programme)
                seen_programmes.add(prog_key)

    if len(root) == 0:
        print("No matching EPG data found; epg.xml not updated.")
        return
    tree = ET.ElementTree(root)
    tree.write("epg.xml", encoding='utf-8', xml_declaration=True)
    step_daddy.epg_data = parsed_epg
    print("EPG generation complete. Saved to epg.xml")