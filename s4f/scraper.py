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
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        # These headers mimic the browser request seen in your logs
        self.scraper.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://sports4free.ru",
            "Referer": "https://sports4free.ru/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        })
        
        self.channels_url = "https://sports4free.ru/channel-api/channels"
        self.groups_url = "https://sports4free.ru/channel-api/groups"
        self.web_base = "https://cdn-bubbles.xyz/hls"
        
        self.output_dir = "s4f"
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        try:
            # 1. Fetch Groups (mapping ID to Name)
            print("Fetching groups...")
            groups_res = self.scraper.get(self.groups_url).json()
            group_map = {str(g['id']): g['name'] for g in groups_res if 'id' in g}
            
            # Small delay to prevent rate-limiting/detection
            time.sleep(2) 

            # 2. Fetch Channels
            print("Fetching channels...")
            channels_res = self.scraper.get(self.channels_url).json()

            if not isinstance(channels_res, list):
                print("Error: API response is not a list.")
                return

        except Exception as e:
            # This captures the "Expecting value" error if Cloudflare blocks the runner
            print(f"Error fetching data: {e}")
            return

        # Sort channels alphabetically by name
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
            
            # Link groupId to the Name from groups.json
            g_id = str(ch.get('groupId', ''))
            group_name = group_map.get(g_id, "OTHER").strip().upper()
            
            # Use the channel ID for the stream link
            ch_id = str(ch.get('id', ''))
            if not ch_id or ch_id == 'None':
                continue
            
            stream_url = f"{self.web_base}?id={ch_id}"
            
            # Create M3U Entry
            entry = f'#EXTINF:-1 tvg-id="{ch_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group_name}",{name}\n{stream_url}'
            m3u_full.append(entry)
            
            # Filter for US channels
            if any(term in group_name for term in ["US|", "UNITED STATES"]) or "US|" in name:
                m3u_us_only.append(entry)

            # EPG XML Generation
            channel_node = ET.SubElement(root, "channel", id=ch_id)
            ET.SubElement(channel_node, "display-name").text = name

        # Save all files to the s4f directory
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
