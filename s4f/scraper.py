import json
import os
import random
import time
from datetime import datetime
import xml.etree.ElementTree as ET
from curl_cffi import requests
from curl_cffi.requests import Session

class Sports4FreeScraper:
    def __init__(self):
        proxy_url = os.getenv("PROXY_URL")  # e.g. http://user:pass@residential-ip:port
        self.proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

        # Use strong browser impersonation
        self.session = Session(impersonate=random.choice([
            "chrome131", "chrome124", "chrome120",
            "edge131", "edge122", "safari18.0"
        ]))

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://sports4free.ru",
            "Referer": "https://sports4free.ru/",
            "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=1",
        })

        self.groups_url = "https://sports4free.ru/channel-api/groups"
        self.channels_url = "https://sports4free.ru/channel-api/channels"
        self.cdn_base = "https://cdn-bubbles.xyz/hls"

        self.output_dir = "s4f"
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_with_retry(self, url: str, max_retries: int = 4) -> requests.Response:
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Fetching {url} (attempt {attempt}/{max_retries})")
                resp = self.session.get(
                    url,
                    proxies=self.proxies,
                    timeout=25,
                )
                resp.raise_for_status()
                return resp
            except Exception as e:
                print(f"Request failed: {e}")
                if attempt == max_retries:
                    raise
                time.sleep(random.uniform(3, 8))  # longer backoff
        raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts")

    def run(self):
        print("Starting scrape...")

        try:
            # Groups first
            groups_resp = self.fetch_with_retry(self.groups_url)
            groups_data = groups_resp.json()
            group_map = {str(g.get("id", "")): str(g.get("name", "UNKNOWN")).strip().upper()
                         for g in groups_data if g.get("id")}

            time.sleep(random.uniform(2.0, 5.0))

            # Channels
            channels_resp = self.fetch_with_retry(self.channels_url)
            channels = channels_resp.json()

            if not isinstance(channels, list):
                raise ValueError("Channels response is not a list")

        except Exception as e:
            print(f"SCRAPE FAILED: {e}")
            if 'groups_resp' in locals():
                print("Groups response preview:", groups_resp.text[:400])
            if 'channels_resp' in locals():
                print("Channels response preview:", channels_resp.text[:400])
            return False

        # Sort channels by name
        channels.sort(key=lambda x: str(x.get("name", "")).lower())

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        m3u_header = f'#EXTM3U x-tvg-url="https://raw.githubusercontent.com/BuddyChewChew/sports/main/s4f/s4f_epg.xml" m3u-updated="{timestamp}"'

        m3u_full = [m3u_header]
        m3u_us = [m3u_header]
        epg_root = ET.Element("tv")

        processed = 0

        for ch in channels:
            if not isinstance(ch, dict):
                continue

            ch_id = str(ch.get("id", "")).strip()
            if not ch_id:
                continue

            name = str(ch.get("name", "Unknown")).strip()
            logo = str(ch.get("logo", "")).strip()
            group_id = str(ch.get("groupId", ""))
            group_name = group_map.get(group_id, "OTHER")

            stream_url = f"{self.cdn_base}?id={ch_id}"

            extinf = (
                f'#EXTINF:-1 tvg-id="{ch_id}" tvg-name="{name}" '
                f'tvg-logo="{logo}" group-title="{group_name}",{name}\n'
                f'{stream_url}'
            )

            m3u_full.append(extinf)

            # US-only variant
            if any(kw in group_name.upper() for kw in ["US|", "UNITED STATES", "USA"]) or "US|" in name.upper():
                m3u_us.append(extinf)

            # EPG entry
            channel_el = ET.SubElement(epg_root, "channel", id=ch_id)
            ET.SubElement(channel_el, "display-name").text = name

            processed += 1

        # Write files
        with open(f"{self.output_dir}/s4f_playlist.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_full))

        with open(f"{self.output_dir}/s4f_us_only.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_us))

        with open(f"{self.output_dir}/s4f_data.json", "w", encoding="utf-8") as f:
            json.dump(channels, f, indent=2, ensure_ascii=False)

        tree = ET.ElementTree(epg_root)
        tree.write(f"{self.output_dir}/s4f_epg.xml", encoding="utf-8", xml_declaration=True)

        print(f"Success → processed {processed} channels")
        return True


if __name__ == "__main__":
    scraper = Sports4FreeScraper()
    success = scraper.run()

    if not success:
        exit(1)
