import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import cloudscraper

class SportsScraper:
    def __init__(self):
        # We use a specific fingerprinted browser to bypass Cloudflare
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        # Adding a common browser User-Agent manually as a backup
        self.scraper.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://sports4free.ru/"
        })
        
        self.channels_url = "https://sports4free.ru/channel-api/channels"
        self.groups_url = "https://sports4free.ru/channel-api/groups"
        self.web_base = "https://cdn-bubbles.xyz/hls"
        
        self.output_dir = "s4f"
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        try:
            # 1. Fetch Groups (with a tiny delay to look human)
            groups_res = self.scraper.get(self.groups_url).json()
            group_map = {str(g['id']): g['name'] for g in groups_res if 'id' in g}
            
            time.sleep(2) 

            # 2. Fetch Channels
            channels_res = self.scraper.get(self.channels_url).json()

            if not isinstance(channels_res, list):
                print("Error: API response is not a list.")
                return

        except Exception as e:
            # This is where your current error "Expecting value..." is caught
            print(f"Error fetching data: {e}")
            return

        # --- Logic for sorting and file generation remains the same ---
        channels_res.sort(key=lambda x: str(x.get('name', '')).lower())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        m3u_header = f'#EXTM3U x-tvg-url="https://raw.githubusercontent.com/BuddyChewChew/sports/main/s4f/s4f_epg.xml" m3u-updated="{timestamp}"'
        
        m3u_full, m3u_us_only = [m3u_header], [m3u_header]
        root = ET.Element("tv")

        for ch in channels_res:
            name, logo = str(ch.get('name', 'Unknown')), str(ch.get('logo', ''))
            group_name = group_map.get(str(ch.get('groupId', '')), "OTHER").upper()
            ext_id = str(ch.get('id', ''))
            
            if not ext_id or ext_id == 'None': continue
            
            stream_url = f"{self.web_base}?id={ext_id}"
            entry = f'#EXTINF:-1 tvg-id="{ext_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group_name}",{name}\n{stream_url}'
            
            m3u_full.append(entry)
            if any(x in group_name for x in ["US|", "UNITED STATES"]) or "US|" in name:
                m3u_us_only.append(entry)

            # EPG Logic
            channel_node = ET.SubElement(root, "channel", id=ext_id)
            ET.SubElement(channel_node, "display-name").text = name

        # Save all files
        with open(os.path.join(self.output_dir, "s4f_playlist.m3u8"), "w") as f: f.write("\n".join(m3u_full))
        with open(os.path.join(self.output_dir, "s4f_us_only.m3u8"), "w") as f: f.write("\n".join(m3u_us_only))
        with open(os.path.join(self.output_dir, "s4f_data.json"), "w") as f: json.dump(channels_res, f, indent=4)
        ET.ElementTree(root).write(os.path.join(self.output_dir, "s4f_epg.xml"), encoding="utf-8", xml_declaration=True)
        
        print(f"Success: Processed {len(m3u_full)-1} channels.")

if __name__ == "__main__":
    SportsScraper().run()
