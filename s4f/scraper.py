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
                # 1. Get Group Names
                groups_res = client.get(self.groups_url)
                groups_data = groups_res.json()
                
                # 2. Get Channels
                channels_res = client.get(self.channels_url)
                channels_data = channels_res.json()

                # SAFETY CHECK: Ensure we actually got lists back from the API 
                if not isinstance(groups_data, list) or not isinstance(channels_data, list):
                    print(f"Error: API did not return a list. Groups type: {type(groups_data)}, Channels type: {type(channels_data)}")
                    return

                # Create a map of IDs to Group Names
                group_map = {str(g['id']): g['name'].strip() for g in groups_data if isinstance(g, dict)}
                
        except Exception as e:
            print(f"Error fetching or parsing data: {e}") [cite: 1]
            return

        # Sort channels alphabetically by name
        channels_data.sort(key=lambda x: x.get('name', '').lower())

        m3u_full = [f'#EXTM3U x-tvg-url="https://raw.githubusercontent.com/BuddyChewChew/sports/main/s4f/s4f_epg.xml"']
        m3u_us_only = [f'#EXTM3U x-tvg-url="https://raw.githubusercontent.com/BuddyChewChew/sports/main/s4f/s4f_epg.xml"']
        root = ET.Element("tv")

        for ch in channels_data:
            if not isinstance(ch, dict): continue
            
            name = ch.get('name', 'Unknown').strip()
            logo = ch.get('logo', '').strip()
            
            # Extract raw ID from the API data
            original_stream = ch.get('stream', '')
            extracted_id = original_stream.split('id=')[-1] if "id=" in original_stream else str(ch.get('tvgId'))
            if not extracted_id: continue
            
            # Set unique_tvg_id to match API ID exactly (no "s4f_" prefix)
            unique_tvg_id = extracted_id
            
            stream_url = f"{self.web_base}?id={unique_tvg_id}&type=.m3u8"
            
            group_id = str(ch.get('groupId', ''))
            group_name = group_map.get(group_id, "OTHER").upper()

            # M3U Entry
            entry = f'#EXTINF:-1 tvg-id="{unique_tvg_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group_name}",{name}\n{stream_url}'

            m3u_full.append(entry)
            if "USA" in group_name or "US|" in name:
                m3u_us_only.append(entry)

            # Build EPG Node
            channel_node = ET.SubElement(root, "channel", id=unique_tvg_id)
            ET.SubElement(channel_node, "display-name").text = name
            prog = ET.SubElement(root, "programme", 
                                start=datetime.now().strftime("%Y%m%d%H0000 +0000"),
                                stop=datetime.now().strftime("%Y%m%d%H5900 +0000"),
                                channel=unique_tvg_id)
            ET.SubElement(prog, "title").text = f"LIVE: {name}"

        # Write all files to the s4f directory
        with open(os.path.join(self.output_dir, "s4f_playlist.m3u8"), "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_full))
        with open(os.path.join(self.output_dir, "s4f_us_only.m3u8"), "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_us_only))
        with open(os.path.join(self.output_dir, "s4f_data.json"), "w", encoding="utf-8") as f:
            json.dump(channels_data, f, indent=4)
        
        tree = ET.ElementTree(root)
        tree.write(os.path.join(self.output_dir, "s4f_epg.xml"), encoding="utf-8", xml_declaration=True)
        print("Success: Playlists and EPG updated with raw API IDs.")

if __name__ == "__main__":
    SportsScraper().run()
