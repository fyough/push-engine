import httpx
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime

class SportsScraper:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.groups_url = "https://my-dev--master-gqd4.diploi.me/api/groups"
        self.channels_url = "https://my-dev--master-gqd4.diploi.me/api/channels"
        self.web_base = "https://my-dev--worker-1-x5wz.diploi.me/hls"
        self.output_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        try:
            with httpx.Client(headers=self.headers, timeout=20.0) as client:
                groups_data = client.get(self.groups_url).json()
                group_map = {str(g['id']): g['name'].strip() for g in groups_data}
                channels_data = client.get(self.channels_url).json()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return

        channels_data.sort(key=lambda x: x.get('name', '').lower())

        m3u_full = [f'#EXTM3U x-tvg-url="https://raw.githubusercontent.com/BuddyChewChew/sports/main/s4f/s4f_epg.xml"']
        m3u_us_only = [f'#EXTM3U x-tvg-url="https://raw.githubusercontent.com/BuddyChewChew/sports/main/s4f/s4f_epg.xml"']
        root = ET.Element("tv")

        for ch in channels_data:
            name = ch.get('name', 'Unknown').strip()
            logo = ch.get('logo', '').strip()
            
            # Use raw ID from API
            original_stream = ch.get('stream', '')
            extracted_id = original_stream.split('id=')[-1] if "id=" in original_stream else str(ch.get('tvgId'))
            if not extracted_id: continue
            
            stream_url = f"{self.web_base}?id={extracted_id}&type=.m3u8"
            
            group_id = str(ch.get('groupId', ''))
            group_name = group_map.get(group_id, "OTHER").upper()
            
            # REMOVED PREFIX: unique_tvg_id is now just the ID number
            unique_tvg_id = extracted_id

            entry = f'#EXTINF:-1 tvg-id="{unique_tvg_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group_name}",{name}\n{stream_url}'

            m3u_full.append(entry)
            if "USA" in group_name or "US|" in name:
                m3u_us_only.append(entry)

            # Build Placeholder EPG with matching ID
            channel_node = ET.SubElement(root, "channel", id=unique_tvg_id)
            ET.SubElement(channel_node, "display-name").text = name
            prog = ET.SubElement(root, "programme", 
                                start=datetime.now().strftime("%Y%m%d%H0000 +0000"),
                                stop=datetime.now().strftime("%Y%m%d%H5900 +0000"),
                                channel=unique_tvg_id)
            ET.SubElement(prog, "title").text = f"LIVE: {name}"

        with open(os.path.join(self.output_dir, "s4f_playlist.m3u8"), "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_full))
        with open(os.path.join(self.output_dir, "s4f_us_only.m3u8"), "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_us_only))
        with open(os.path.join(self.output_dir, "s4f_data.json"), "w", encoding="utf-8") as f:
            json.dump(channels_data, f, indent=4)
        
        tree = ET.ElementTree(root)
        tree.write(os.path.join(self.output_dir, "s4f_epg.xml"), encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    SportsScraper().run()
