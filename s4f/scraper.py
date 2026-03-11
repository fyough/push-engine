import httpx
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime

class SportsScraper:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0"}
        # These are your source APIs
        self.channels_url = "https://my-dev--master-gqd4.diploi.me/api/channels"
        self.web_base = "https://my-dev--worker-1-x5wz.diploi.me/hls"
        self.output_dir = "s4f"
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        try:
            with httpx.Client(headers=self.headers, timeout=30.0) as client:
                # We only need the channels API because the group names are already inside it
                channels_res = client.get(self.channels_url).json()

                if not isinstance(channels_res, list):
                    print("Error: API did not return a list of channels.")
                    return

        except Exception as e:
            print(f"Error fetching data: {e}")
            return

        # Sort channels alphabetically by name
        channels_res.sort(key=lambda x: str(x.get('name', '')).lower() if isinstance(x, dict) else "")

        # Create a timestamp to force GitHub to see a change every hour
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        m3u_header = f'#EXTM3U x-tvg-url="https://raw.githubusercontent.com/BuddyChewChew/sports/main/s4f/s4f_epg.xml" m3u-updated="{timestamp}"'
        
        m3u_full = [m3u_header]
        m3u_us_only = [m3u_header]
        root = ET.Element("tv")

        for ch in channels_res:
            if not isinstance(ch, dict): continue
            
            # READ DATA FROM JSON
            name = str(ch.get('name', 'Unknown')).strip()
            logo = str(ch.get('logo', '')).strip()
            
            # Use the 'group' field directly as provided in your JSON
            group_name = str(ch.get('group', 'OTHER')).strip().upper()
            
            # ID Extraction for the stream URL
            original_stream = str(ch.get('stream', ''))
            extracted_id = original_stream.split('id=')[-1] if "id=" in original_stream else str(ch.get('tvgId', ''))
            
            if not extracted_id or extracted_id == 'None':
                continue
            
            # Construct the local stream URL
            stream_url = f"{self.web_base}?id={extracted_id}&type=.m3u8"
            
            # BUILD M3U ENTRY
            entry = f'#EXTINF:-1 tvg-id="{extracted_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group_name}",{name}\n{stream_url}'
            m3u_full.append(entry)
            
            # US Filter: Check the group name or the channel name for "US"
            if "US|" in group_name or "UNITED STATES" in group_name or "US|" in name:
                m3u_us_only.append(entry)

            # EPG XML Generation
            channel_node = ET.SubElement(root, "channel", id=extracted_id)
            ET.SubElement(channel_node, "display-name").text = name
            prog = ET.SubElement(root, "programme", 
                                start=datetime.now().strftime("%Y%m%d%H0000 +0000"),
                                stop=datetime.now().strftime("%Y%m%d%H5900 +0000"),
                                channel=extracted_id)
            ET.SubElement(prog, "title").text = f"LIVE: {name}"

        # SAVE ALL FILES
        with open(os.path.join(self.output_dir, "s4f_playlist.m3u8"), "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_full))
        with open(os.path.join(self.output_dir, "s4f_us_only.m3u8"), "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_us_only))
        with open(os.path.join(self.output_dir, "s4f_data.json"), "w", encoding="utf-8") as f:
            json.dump(channels_res, f, indent=4)
        
        tree = ET.ElementTree(root)
        tree.write(os.path.join(self.output_dir, "s4f_epg.xml"), encoding="utf-8", xml_declaration=True)
        print(f"Success: Processed {len(m3u_full)-1} channels with correct group titles.")

if __name__ == "__main__":
    SportsScraper().run()
