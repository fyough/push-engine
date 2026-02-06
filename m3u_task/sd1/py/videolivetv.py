import os
import urllib.parse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import random
import time
import json

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/126.0.6478.35 Mobile/15E148 Safari/604.1'
]

channel_logos = {
    "A&E": "https://cdn.tvpassport.com/image/station/960x540/v2/s10036_h15_aa.png",
    "ACC Network": "https://cdn.tvpassport.com/image/station/240x135/v2/s111905_h15_ac.png",
    "AMC": "https://cdn.tvpassport.com/image/station/240x135/v2/s52247_h15_aa.png",
    "American Heroes Channel": "https://cdn.tvpassport.com/image/station/240x135/v2/s18284_h15_aa.png",
    "Animal Planet": "https://cdn.tvpassport.com/image/station/240x135/v2/s16331_h9_ad.png",
    "BBC America": "https://cdn.tvpassport.com/image/station/240x135/v2/s18332_h15_aa.png",
    "BBC World News HD": "https://cdn.tvpassport.com/image/station/240x135/v2/s89542_h15_ab.png",
    "BET": "https://cdn.tvpassport.com/image/station/240x135/v2/s10051_h15_ad.png",
    "BET Her": "https://cdn.tvpassport.com/image/station/240x135/v2/s14897_h15_ac.png",
    "Big Ten Network": "https://cdn.tvpassport.com/image/station/240x135/v2/s56783_h15_ab.png",
    "Bloomberg TV": "https://cdn.tvpassport.com/image/station/240x135/v2/s71799_h15_ab.png",
    "Boomerang": "https://cdn.tvpassport.com/image/station/240x135/v2/s21883_h15_ab.png",
    "Bravo": "https://cdn.tvpassport.com/image/station/240x135/v2/s10057_h15_ab.png",
    "Cartoon Network": "https://cdn.tvpassport.com/image/station/240x135/v2/s60048_h15_ac.png",
    "CBS Sports Network": "https://cdn.tvpassport.com/image/station/240x135/v2/s16365_h15_ae.png",
    "Cinemax": "https://cdn.tvpassport.com/image/station/240x135/v2/s10120_h15_ab.png",
    "CNBC": "https://cdn.tvpassport.com/image/station/240x135/v2/s10139_h15_ad.png",
    "CMT": "https://cdn.tvpassport.com/image/station/240x135/v2/s15072_h15_aa.png",
    "CNN": "https://cdn.tvpassport.com/image/station/240x135/v2/s10142_h15_aa.png",
    "Comedy Central": "https://cdn.tvpassport.com/image/station/240x135/v2/s10149_h15_ab.png",
    "Cooking Channel": "https://cdn.tvpassport.com/image/station/240x135/v2/s30156_h15_aa.png",
    "Crime & Investigation HD": "https://cdn.tvpassport.com/image/station/240x135/v2/s61469_h15_ab.png",
    "CSPAN": "https://cdn.tvpassport.com/image/station/240x135/v2/s10161_h15_ad.png",
    "CSPAN 2": "https://cdn.tvpassport.com/image/station/240x135/v2/s10162_h15_ac.png",
    "Destination America": "https://cdn.tvpassport.com/image/station/240x135/v2/s16617_h15_aa.png",
    "Discovery": "https://cdn.tvpassport.com/image/station/240x135/v2/s11150_h15_af.png",
    "Discovery Family Channel": "https://cdn.tvpassport.com/image/station/240x135/v2/s16618_h15_aa.png",
    "Discovery Life": "https://cdn.tvpassport.com/image/station/240x135/v2/s16125_h15_ac.png",
    "Disney Channel (East)": "https://cdn.tvpassport.com/image/station/240x135/v2/s10171_h15_ae.png",
    "Disney Junior": "https://cdn.tvpassport.com/image/station/240x135/v2/s74885_h15_ab.png",
    "Disney XD": "https://cdn.tvpassport.com/image/station/240x135/v2/s18279_h15_aa.png",
    "E!": "https://cdn.tvpassport.com/image/station/240x135/v2/s10989_h15_aa.png",
    "ESPN": "https://cdn.tvpassport.com/image/station/240x135/v2/s10179_h15_aa.png",
    "ESPN2": "https://cdn.tvpassport.com/image/station/240x135/v2/s12444_h15_ab.png",
    "ESPNews": "https://cdn.tvpassport.com/image/station/240x135/v2/s16485_h15_aa.png",
    "ESPNU": "https://cdn.tvpassport.com/image/station/240x135/v2/s45654_h15_aa.png",
    "Food Network": "https://cdn.tvpassport.com/image/station/240x135/v2/s12574_h15_ab.png",
    "Fox Business Network": "https://cdn.tvpassport.com/image/station/240x135/v2/s58649_h15_ac.png",
    "FOX News Channel": "https://cdn.tvpassport.com/image/station/240x135/v2/s16374_h15_ab.png",
    "FOX Sports 1": "https://cdn.tvpassport.com/image/station/240x135/v2/s82541_h15_ab.png",
    "FOX Sports 2": "https://cdn.tvpassport.com/image/station/240x135/v2/s33178_h15_ab.png",
    "Freeform": "https://cdn.tvpassport.com/image/station/240x135/v2/s10093_h15_ae.png",
    "Fuse HD": "https://cdn.tvpassport.com/image/station/240x135/v2/s59116_h15_ac.png",
    "FX": "https://cdn.tvpassport.com/image/station/240x135/v2/s58574_h15_aa.png",
    "FX Movie": "https://cdn.tvpassport.com/image/station/240x135/v2/s70253_h15_aa.png",
    "FXX": "https://cdn.tvpassport.com/image/station/240x135/v2/s17927_h15_aa.png",
    "FYI": "https://cdn.tvpassport.com/image/station/240x135/v2/s58988_h15_aa.png",
    "Golf Channel": "https://cdn.tvpassport.com/image/station/240x135/v2/s65384_h15_aa.png",
    "Hallmark": "https://cdn.tvpassport.com/image/station/240x135/v2/s66268_h15_ab.png",
    "Hallmark Drama HD": "https://cdn.tvpassport.com/image/station/240x135/v2/s105756_h15_ab.png",
    "Hallmark Movies & Mysteries HD": "https://cdn.tvpassport.com/image/station/240x135/v2/s61522_h15_ab.png",
    "HBO 2 East": "https://cdn.tvpassport.com/image/station/240x135/v2/s59368_h15_aa.png",
    "HBO Comedy HD": "https://cdn.tvpassport.com/image/station/240x135/v2/s18429_h15_aa.png",
    "HBO East": "https://cdn.tvpassport.com/image/station/240x135/v2/s10240_h15_aa.png",
    "HBO Family East": "https://cdn.tvpassport.com/image/station/240x135/v2/s16585_h15_aa.png",
    "HBO Signature": "https://cdn.tvpassport.com/image/station/240x135/v2/s59363_h15_aa.png",
    "HBO Zone HD": "https://cdn.tvpassport.com/image/station/240x135/v2/s59845_h15_aa.png",
    "HGTV": "https://cdn.tvpassport.com/image/station/240x135/v2/s14902_h15_ab.png",
    "History": "https://cdn.tvpassport.com/image/station/240x135/v2/s57708_h15_ad.png",
    "HLN": "https://cdn.tvpassport.com/image/station/240x135/v2/s10145_h15_ac.png",
    "IFC": "https://cdn.tvpassport.com/image/station/240x135/v2/s14873_h15_ac.png",
    "Investigation Discovery": "https://cdn.tvpassport.com/image/station/240x135/v2/s16615_h15_ad.png",
    "ION Television East HD": "https://cdn.tvpassport.com/image/station/240x135/v2/s18633_h15_ac.png",
    "Lifetime": "https://cdn.tvpassport.com/image/station/240x135/v2/s10918_h15_ac.png",
    "LMN": "https://cdn.tvpassport.com/image/station/240x135/v2/s55887_h15_ag.png",
    "Logo": "https://cdn.tvpassport.com/image/station/240x135/v2/s46762_h15_aa.png",
    "MeTV Toons":"https://cdn.tvpassport.com/image/station/240x135/v2/s159817_h15_aa.png",
    "MLB Network": "https://cdn.tvpassport.com/image/station/240x135/v2/s62079_h15_aa.png",
    "MoreMAX": "https://cdn.tvpassport.com/image/station/240x135/v2/s59373_h15_ad.png",
    "MotorTrend HD": "https://cdn.tvpassport.com/image/station/240x135/v2/s31046_h15_ab.png",
    "MovieMAX": "https://cdn.tvpassport.com/image/station/240x135/v2/s59963_h15_ab.png",
    "MSNBC": "https://cdn.tvpassport.com/image/station/240x135/v2/s16300_h15_ac.png",
    "MTV": "https://cdn.tvpassport.com/image/station/240x135/v2/s10986_h15_aa.png",
    "Nat Geo WILD": "https://cdn.tvpassport.com/image/station/240x135/v2/s66804_h15_ab.png",
    "National Geographic": "https://cdn.tvpassport.com/image/station/240x135/v2/s49438_h15_ab.png",
    "NBA TV": "https://cdn.tvpassport.com/image/station/240x135/v2/s32281_h15_ad.png",
    "Newsmax TV": "https://cdn.tvpassport.com/image/station/240x135/v2/s87925_h15_ac.png",
    "NFL Network": "https://cdn.tvpassport.com/image/station/240x135/v2/s34710_h15_aa.png",
    "NFL Red Zone": "https://cdn.tvpassport.com/image/station/240x135/v2/s65024_h9_aa.png",
    "NHL Network": "https://cdn.tvpassport.com/image/station/240x135/v2/s58570_h15_ab.png",
    "Nick Jr.": "https://cdn.tvpassport.com/image/station/240x135/v2/s82649_h15_ad.png",
    "Nickelodeon East": "https://cdn.tvpassport.com/image/station/240x135/v2/s11006_h15_ab.png",
    "Nicktoons": "https://cdn.tvpassport.com/image/station/240x135/v2/s82654_h15_ac.png",
    "Outdoor Channel": "https://cdn.tvpassport.com/image/station/240x135/v2/s14776_h15_ab.png",
    "OWN": "https://cdn.tvpassport.com/image/station/240x135/v2/s70387_h15_aa.png",
    "Oxygen True Crime": "https://cdn.tvpassport.com/image/station/240x135/v2/s21484_h15_ac.png",
    "PBS 13 (WNET) New York": "https://cdn.tvpassport.com/image/station/240x135/v2/s11039_h15_ab.png",
    "ReelzChannel": "https://cdn.tvpassport.com/image/station/240x135/v2/s52199_h9_ac.png",
    "Science": "https://cdn.tvpassport.com/image/station/240x135/v2/s57390_h15_ac.png",
    "SEC Network": "https://cdn.tvpassport.com/image/station/240x135/v2/s89535_h15_ab.png",
    "Showtime (E)": "https://cdn.tvpassport.com/image/station/240x135/v2/s11115_h15_aa.png",
    "SHOWTIME 2": "https://cdn.tvpassport.com/image/station/240x135/v2/s11116_h15_aa.png",
    "STARZ East": "https://cdn.tvpassport.com/image/station/240x135/v2/s12719_h15_ac.png",
    "SundanceTV HD": "https://cdn.tvpassport.com/image/station/240x135/v2/s71280_h15_aa.png",
    "SYFY": "https://cdn.tvpassport.com/image/station/240x135/v2/s11097_h15_ae.png",
    "TBS": "https://cdn.tvpassport.com/image/station/240x135/v2/s11867_h15_ac.png",
    "TCM": "https://cdn.tvpassport.com/image/station/240x135/v2/s48815_h15_ab.png",
    "TeenNick": "https://cdn.tvpassport.com/image/station/240x135/v2/s59036_h15_ac.png",
    "Telemundo East": "https://cdn.tvpassport.com/image/station/240x135/v2/s73245_h15_ac.png",
    "Tennis Channel": "https://cdn.tvpassport.com/image/station/240x135/v2/s33395_h15_ac.png",
    "The CW (WPIX New York)": "https://cdn.tvpassport.com/image/station/240x135/v2/s53098_h15_ac.png",
    "The Movie Channel East": "https://cdn.tvpassport.com/image/station/240x135/v2/s35329_h15_aa.png",
    "The Weather Channel": "https://cdn.tvpassport.com/image/station/240x135/v2/s11187_h15_aa.png",
    "TLC": "https://cdn.tvpassport.com/image/station/240x135/v2/s11158_h15_ad.png",
    "TNT": "https://cdn.tvpassport.com/image/station/240x135/v2/s11164_h15_ac.png",
    "Travel Channel": "https://cdn.tvpassport.com/image/station/240x135/v2/s11180_h15_ac.png",
    "truTV": "https://cdn.tvpassport.com/image/station/240x135/v2/s10153_h15_ad.png",
    "TV One HD": "https://cdn.tvpassport.com/image/station/240x135/v2/s61960_h15_ab.png",
    "Universal Kids": "https://cdn.tvpassport.com/image/station/240x135/v2/s70225_h15_ae.png",
    "Univision East": "https://cdn.tvpassport.com/image/station/240x135/v2/s11118_h15_ab.png",
    "USA Network": "https://cdn.tvpassport.com/image/station/240x135/v2/s11207_h15_af.png",
    "VH1": "https://cdn.tvpassport.com/image/station/240x135/v2/s11218_h15_ac.png",
    "VICE": "https://cdn.tvpassport.com/image/station/240x135/v2/s18822_h15_ac.png",
    "WABC (New York) ABC East": "https://github.com/BuddyChewChew/My-Streams/blob/main/Logos/tv/abc-blue-us.png?raw=true",
    "WCBS (New York) CBS East": "https://github.com/BuddyChewChew/My-Streams/blob/main/Logos/tv/cbs-logo-white-us.png?raw=true",
    "WE tv": "https://cdn.tvpassport.com/image/station/240x135/v2/s59296_h15_aa.png",
    "WNBC (New York) NBC East": "https://github.com/BuddyChewChew/My-Streams/blob/main/Logos/tv/nbc-logo-alt-us.png?raw=true",
    "WNYW (New York) FOX East": "https://github.com/BuddyChewChew/My-Streams/blob/main/Logos/tv/FOXRED.png?raw=true"
}

def main():
    # SETTINGS: Points to your new fyough/watch repository
    epg_url = "https://raw.githubusercontent.com/fyough/watch/main/sd1/en/videoall.xml"
    offline_url = "https://github.com/fyough/watch/raw/main/en/offline.mp4"
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    chrome_service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", fix_hairline=True)

    driver.get("https://thetvapp.to/")
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "row")))

    # Focus strictly on Live TV Channels section
    live_tv_row = driver.find_element(By.XPATH, "//h3[contains(text(), 'Live TV Channels')]/..")
    links = live_tv_row.find_elements(By.TAG_NAME, "a")
    live_tv_links = [(link.text.strip(), link.get_attribute("href")) for link in links]

    # Header is now added in GitHub Actions workflow - do not print it here
    print("")  # optional empty line before first channel

    for name, link in live_tv_links:
        driver.get(link)
        time.sleep(5)
        
        network_requests = json.loads(driver.execute_script("return JSON.stringify(performance.getEntries());"))
        logo_url = channel_logos.get(name, "")
        
        m3u8_urls = [req["name"] for req in network_requests if ".m3u8" in req["name"]]
        
        final_url = offline_url
        if m3u8_urls:
            url = m3u8_urls[0]
            if "ping.gif" in url and "mu=" in url:
                parsed = urllib.parse.urlparse(url)
                final_url = urllib.parse.unquote(urllib.parse.parse_qs(parsed.query)["mu"][0])
            else:
                final_url = url

        print(f'#EXTINF:-1 group-title="SD1 CHANNELS" tvg-id="{name}" tvg-name="{name}" tvg-logo="{logo_url}", {name}')
        print(final_url)

    driver.quit()

if __name__ == "__main__":
    main()
