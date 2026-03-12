import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import cloudscraper

class SportsScraper:
    def __init__(self):
        # cloudscraper uses a specialized request adapter to bypass Cloudflare
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'firefox',
                'platform': 'windows',
                'desktop': True
            }
        )
        # Mimicking the exact headers from your browser logs
        self.scraper.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://sports4free.ru",
            "Referer": "https://sports4free.ru/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=4"
        })
        
        self.channels_url = "https://sports4free.ru/channel-api/channels"
        self.groups_url = "https://sports4free.ru/channel-api/groups"
        self.web_base = "https://cdn-bubbles.xyz/hls"
        
        self.output_dir = "s4f"
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        try:
            print("Fetching groups...")
            groups_resp = self.scraper.get(self.groups_url)
            groups_resp.raise_for_status() # Check for 403/503 errors
            groups_data = groups_resp.json()
            group_map = {str(g['id']): g['name'] for g in groups_data if 'id' in g}
            
            # Delay to mimic human browsing speed
            time.sleep(2.5) 

            print("Fetching channels...")
            channels_resp = self.scraper.get(self.channels_url)
            channels_resp.raise_for_status()
            channels_res = channels_resp.json()

            if not isinstance(channels_res, list):
                print("Error: API response is not a list.")
                return

        except Exception as e:
            # This captures the Cloudflare block without crashing the whole process
            print(f"FAILED to bypass Cloudflare: {e}")
            if 'resp' in locals():
                print(f"Response snippet: {groups_resp.text[:200]}")
            return

        # Sort channels alphabetically
        channels_res.sort(key=lambda x: str(x.get('name', '')).lower() if isinstance(x, dict) else "")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        m3u_header = f'#EXTM3U x-tvg-url="https://raw.githubusercontent.com/BuddyChewChew/sports/main/s4f/s4f_epg.xml" m3u-updated="{timestamp}"'
        
        m3u_full = [m3u_header]
        m3u_us_only = [m3u_header]
        root = ET.Element("tv")

        for ch in channels_res:
            if not isinstance(ch, dict): continue
            
            name = str(ch.get('name', 'Unknown')).strip()
            logo = str(ch.get('logo', '')).strip()
            
            # Map groupId to group name
            g_id = str(ch.get('groupId', ''))
            group_name = group_map.get(g_id, "OTHER").strip().upper()
            
            # Extract ID for the CDN URL
            ch_id = str(ch.get('id', ''))
            if not ch_id or ch_id == 'None':
                continue
            
            stream_url = f"{self.web_base}?id={ch_id}"
            
            # Build M3U entry
            entry = f'#EXTINF:-1 tvg-id="{ch_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group_name}",{name}\n{stream_url}'
            m3u_full.append(entry)
            
            if any(term in group_name for term in ["US|", "UNITED STATES"]) or "US|" in name:
                m3u_us_only.append(entry)

            # EPG XML Generation
            channel_node = ET.SubElement(root, "channel", id=ch_id)
            ET.SubElement(channel_node, "display-name").text = name

        # Final File Writing
        with open(os.path.join(self.output_dir, "s4f_playlist.m3u8"), "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_full))
        with open(os.path.join(self.output_dir, "s4f_us_only.m3u8"), "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_us_only))
        with open(os.path.join(self.output_dir, "s4f_data.json"), "w", encoding="utf-8") as f:
            json.dump(channels_res, f, indent=4)
        
        tree = ET.ElementTree(root)
        tree.write(os.path.join(self.output_dir, "s4f_epg.xml"), encoding="utf-8", xml_declaration=True)
        print(f"Success: Processed {len(m3u_full)-1} channels.")

if __name__ == "__main__":
    SportsScraper().run()
