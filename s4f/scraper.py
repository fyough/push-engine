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
        self.output_dir = "s4f"
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        try:
            with httpx.Client(headers=self.headers, timeout=20.0) as client:
                groups_res = client.get(self.groups_url).json()
                channels_res = client.get(self.channels_url).json()

                # DATA SAFEGUARD: Verify we have lists of dictionaries
                if not isinstance(groups_res, list) or not isinstance(channels_res, list):
                    print("Error: API did not return valid lists. Check API health.")
                    return

                group_map = {}
                for g in groups_res:
                    if isinstance(g, dict):
                        g_id = str(g.get('id', '')).strip()
                        g_name = str(g.get('name', 'OTHER')).strip()
                        group_map[g_id] = g_name

        except Exception as e:
            print(f"Error fetching data: {e}")
            return

        # Sort channels alphabetically
        channels_res.sort(key=lambda x: str(x.get('name', '')).lower() if isinstance(x, dict) else "")

        m3u_full = [f'#EXTM3U x-tvg-url="https://raw.githubusercontent.com/BuddyChewChew/sports/main/s4f/s4f_epg.xml"']
        m3u_us_only = [f'#EXTM3U x-tvg-url="https://raw.githubusercontent.com/BuddyChewChew/sports/main/s4f/s4f_epg.xml"']
        root = ET.Element("tv")

        for ch in channels_res:
            if not isinstance(ch, dict): continue
            
            name = str(ch.get('name', 'Unknown')).strip()
            logo = str(ch.get('logo', '')).strip()
            
            original_stream = str(ch.get('stream', ''))
            extracted_id = original_stream.split('id=')[-1] if "id=" in original_stream else str(ch.get('tvgId', ''))
            if not extracted_id or extracted_id == 'None': continue
            
            unique_tvg_id = extracted_id
            stream_url = f"{self.web_base}?id={unique_tvg_id}&type=.m3u8"
            
            raw_group_id = str(ch.get('groupId', '')).strip()
            group_name = group_map.get(raw_group_id, "OTHER").upper()
            
            entry = f'#EXTINF:-1 tvg-id="{unique_tvg_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group_name}",{name}\n{stream_url}'

            m3u_full.append(entry)
            if any(x in group_name for x in ["USA", "UNITED STATES"]) or "US|" in name:
                m3u_us_only.append(entry)

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
            json.dump(channels_res, f, indent=4)
        
        tree = ET.ElementTree(root)
        tree.write(os.path.join(self.output_dir, "s4f_epg.xml"), encoding="utf-8", xml_declaration=True)
        print(f"Success: Processed {len(m3u_full)-1} channels.")

if __name__ == "__main__":
    SportsScraper().run()
