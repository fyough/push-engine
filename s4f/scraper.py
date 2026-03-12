import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
import cloudscraper

class SportsScraper:
    def __init__(self):
        # Cloudscraper handles the Cloudflare 'Challenge' automatically
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'firefox',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # New production endpoints
        self.channels_url = "https://sports4free.ru/channel-api/channels"
        self.groups_url = "https://sports4free.ru/channel-api/groups"
        self.web_base = "https://cdn-bubbles.xyz/hls"
        
        self.output_dir = "s4f"
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        try:
            # 1. Map group IDs to names (e.g., "1" -> "US | SPORTS")
            groups_res = self.scraper.get(self.groups_url).json()
            group_map = {str(g['id']): g['name'] for g in groups_res if 'id' in g}

            # 2. Fetch channel list
            channels_res = self.scraper.get(self.channels_url).json()

            if not isinstance(channels_res, list):
                print("Error: API did not return a list of channels.")
                return

        except Exception as e:
            print(f"Error fetching data: {e}")
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
            
            # Match group ID to name
            group_id = str(ch.get('groupId', ''))
            group_name = group_map.get(group_id, "OTHER").strip().upper()
            
            extracted_id = str(ch.get('id', ''))
            if not extracted_id or extracted_id == 'None':
                continue
            
            # Construct the new CDN stream URL
            stream_url = f"{self.web_base}?id={extracted_id}"
            
            # Build M3U Entry
            entry = f'#EXTINF:-1 tvg-id="{extracted_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group_name}",{name}\n{stream_url}'
            m3u_full.append(entry)
            
            # US Filter
            if any(term in group_name for term in ["US|", "UNITED STATES"]) or "US|" in name:
                m3u_us_only.append(entry)

            # EPG XML Generation
            channel_node = ET.SubElement(root, "channel", id=extracted_id)
            ET.SubElement(channel_node, "display-name").text = name
            prog = ET.SubElement(root, "programme", 
                                start=datetime.now().strftime("%Y%m%d%H0000 +0000"),
                                stop=datetime.now().strftime("%Y%m%d%H5900 +0000"),
                                channel=extracted_id)
            ET.SubElement(prog, "title").text = f"LIVE: {name}"

        # Write files
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
