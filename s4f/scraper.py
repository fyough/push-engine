def run(self):
        try:
            with httpx.Client(headers=self.headers, timeout=20.0) as client:
                # Get Group Names
                groups_res = client.get(self.groups_url)
                groups_data = groups_res.json()
                
                # Get Channels
                channels_res = client.get(self.channels_url)
                channels_data = channels_res.json()

                # SAFETY CHECK: Ensure we actually got lists back from the API
                if not isinstance(groups_data, list) or not isinstance(channels_data, list):
                    print(f"Error: API did not return a list. Groups type: {type(groups_data)}, Channels type: {type(channels_data)}")
                    return

                group_map = {str(g['id']): g['name'].strip() for g in groups_data if isinstance(g, dict)}
                
        except Exception as e:
            print(f"Error fetching or parsing data: {e}")
            return

        # ... (rest of your sorting and file writing code)
