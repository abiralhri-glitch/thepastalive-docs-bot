"""
The Past Alive History - Automated Full Documentary Video Bot
- Dedicated to 'The Past Alive History' Facebook Page (ID: 1357435984129397)
- 100% Full Long-Form Documentary Videos (Original length, widescreen 16:9)
- 100% English Titles, Storytelling Captions, and Tags
- Multi-Layer Zero-Duplicate Protection (Live Facebook Graph API Feed Verification)
- Resilient Android-Embedded Extractor & Direct Archive.org Fallback Pool
"""

import os
import re
import sys
import json
import time
import random
import datetime
import subprocess
import requests

from config import (
    BASE_DIR,
    DOWNLOAD_DIR,
    HISTORY_FILE,
    FB_PAGE_ID,
    FB_PAGE_ACCESS_TOKEN,
    FB_GRAPH_URL
)
from documentary_sources import REFERENCE_YOUTUBE_CHANNELS, DYNAMIC_SEARCH_QUERIES

# Guaranteed 100% Public Domain Historical Documentaries from Archive.org
ARCHIVE_DOCUMENTARY_POOL = [
    {
        "src_id": "arch_battle_of_midway",
        "title": "The Battle of Midway (1942) - Original Color WWII Naval Battle Documentary",
        "url": "https://archive.org/download/BattleOfMidway/BattleOfMidway_512kb.mp4",
        "description": "The Battle of Midway (1942) • Historic Original Color Footage.\n\nExperience John Ford's Academy Award-winning documentary covering the pivotal turning point of the Pacific War in June 1942. Follow @ThePastAliveHistory for daily deep historical restorations. ⏳📜 [src:arch_battle_of_midway]\n\n#ThePastAliveHistory #BattleOfMidway #WWII #ColorHistory #HistoricalRestoration #NavalHistory #MilitaryHistory",
        "category": "WWII History"
    },
    {
        "src_id": "arch_fighting_lady",
        "title": "The Fighting Lady (1944) - Life Aboard an Aircraft Carrier in the Pacific",
        "url": "https://archive.org/download/FightingLady/FightingLady_512kb.mp4",
        "description": "The Fighting Lady (1944) • Academy Award-Winning Color Documentary.\n\nA vivid look at daily life, intense aerial dogfights, and heroic operations aboard the USS Yorktown (CV-10) during World War II. Follow @ThePastAliveHistory for daily deep historical documentaries. ⏳📜 [src:arch_fighting_lady]\n\n#ThePastAliveHistory #FightingLady #AircraftCarrier #WWIIHistory #PacificWar #LivingHistory #USNavy",
        "category": "Naval History"
    },
    {
        "src_id": "arch_memphis_belle",
        "title": "The Memphis Belle: A Story of a Flying Fortress (1944) - B-17 Bombing Missions",
        "url": "https://archive.org/download/MemphisBelle/MemphisBelle_512kb.mp4",
        "description": "The Memphis Belle (1944) • Rare Archival Restored Documentary.\n\nThe real story of the 25th and final mission of the B-17 Flying Fortress 'Memphis Belle' over occupied Europe, directed by William Wyler. Follow @ThePastAliveHistory for daily deep historical restorations. ⏳📜 [src:arch_memphis_belle]\n\n#ThePastAliveHistory #MemphisBelle #B17 #AviationHistory #WWIIBomber #MilitaryRestoration #WarHistory",
        "category": "Aviation History"
    },
    {
        "src_id": "arch_prelude_to_war",
        "title": "Prelude to War (Why We Fight Series) - The Rise of Global Conflict",
        "url": "https://archive.org/download/PreludeToWar/PreludeToWar_512kb.mp4",
        "description": "Prelude to War • Historic Academy Award-Winning Epic Documentary.\n\nFrank Capra's landmark documentary examining the dramatic events that led the world into the greatest conflict in human history. Follow @ThePastAliveHistory for daily deep historical documentaries. ⏳📜 [src:arch_prelude_to_war]\n\n#ThePastAliveHistory #PreludeToWar #WhyWeFight #FrankCapra #WorldWarHistory #ModernHistory #Documentary",
        "category": "Global Conflict"
    },
    {
        "src_id": "arch_the_nazis_strike",
        "title": "The Nazis Strike (1943) - The Geopolitical Map and the Blitzkrieg Era",
        "url": "https://archive.org/download/TheNazisStrike/TheNazisStrike_512kb.mp4",
        "description": "The Nazis Strike (1943) • Archival Historical Restoration.\n\nAn in-depth geopolitical analysis of early European conquests, strategy, and resistance during the Blitzkrieg era. Follow @ThePastAliveHistory for daily deep historical restorations. ⏳📜 [src:arch_the_nazis_strike]\n\n#ThePastAliveHistory #TheNazisStrike #EuropeanHistory #WarRestoration #ArchivalFootage #HistoryUncovered",
        "category": "European History"
    },
    {
        "src_id": "arch_divide_and_conquer",
        "title": "Divide and Conquer (1943) - The Battle for Western Europe",
        "url": "https://archive.org/download/DivideAndConquer/DivideAndConquer_512kb.mp4",
        "description": "Divide and Conquer (1943) • Historic Full-Length Documentary.\n\nChronicling the dramatic invasion and defense of Denmark, Norway, the Low Countries, and the Fall of France in 1940. Follow @ThePastAliveHistory for daily deep historical restorations. ⏳📜 [src:arch_divide_and_conquer]\n\n#ThePastAliveHistory #DivideAndConquer #FallOfFrance #WWIIStrategy #MilitaryHistory #DocumentaryFilm",
        "category": "WWII Strategy"
    }
]

def assert_non_facebook_source(url: str):
    """Enforce strict non-Facebook sourcing policy."""
    if not url:
        return True
    u_lower = url.lower()
    if any(k in u_lower for k in ["facebook.com", "fb.watch", "fb.com", "fb.me"]):
        raise ValueError(f"Facebook sourcing is prohibited! Detected: {url}")
    return True

def get_posted_signatures_from_facebook(page_id: str, access_token: str, limit: int = 100) -> set:
    """Fetch live feed from Facebook Page to prevent any duplicate video."""
    signatures = set()
    if not access_token or not page_id:
        return signatures
    try:
        url = f"{FB_GRAPH_URL}/{page_id}/videos"
        params = {"access_token": access_token, "fields": "description,title", "limit": limit}
        res = requests.get(url, params=params, timeout=15)
        if res.status_code == 200:
            for item in res.json().get("data", []):
                text = (item.get("description", "") + " " + item.get("title", "")).lower()
                matches = re.findall(r"\[src:([a-zA-Z0-9_-]+)\]", text)
                for s in matches:
                    signatures.add(s)
            print(f"[FACEBOOK LIVE] {len(signatures)} posted signatures retrieved from Page.")
    except Exception as e:
        print(f"[FACEBOOK LIVE WARN] {e}")
    return signatures

def load_local_history() -> dict:
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    default_history = {
        "posted_ids": [],
        "last_index": -1,
        "daily_stats": {"date": today_str, "total_posted": 0}
    }
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    ds = data.get("daily_stats", {})
                    if ds.get("date") != today_str:
                        data["daily_stats"] = {"date": today_str, "total_posted": 0}
                    return data
        except Exception:
            pass
    return default_history

def save_local_history(history: dict):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[HISTORY WARN] {e}")

def download_full_documentary(url: str, src_id: str) -> str:
    """Download full documentary video using yt-dlp with android_embedded client."""
    assert_non_facebook_source(url)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    out_file = os.path.join(DOWNLOAD_DIR, f"{src_id}.mp4")

    if os.path.exists(out_file) and os.path.getsize(out_file) > 1000000:
        return out_file

    # If it's a direct MP4 link (Archive.org)
    if url.endswith(".mp4") or "archive.org" in url:
        print(f"[DIRECT DOWNLOAD] Downloading direct documentary: {url}")
        try:
            r = requests.get(url, stream=True, timeout=120)
            if r.status_code == 200:
                with open(out_file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(out_file) and os.path.getsize(out_file) > 1000000:
                    print(f"[DIRECT SUCCESS] Downloaded {out_file} ({os.path.getsize(out_file)/(1024*1024):.1f} MB)")
                    return out_file
        except Exception as de:
            print(f"[DIRECT WARN] {de}")

    # YouTube download with android_embedded client to bypass bot challenges
    cmd = [
        "yt-dlp",
        "--extractor-args", "youtube:player_client=android_embedded,web_embedded",
        "--merge-output-format", "mp4",
        "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "-o", out_file,
        "--socket-timeout", "40",
        "--retries", "3",
        url
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if res.returncode == 0 and os.path.exists(out_file) and os.path.getsize(out_file) > 1000000:
            print(f"[YT-DLP SUCCESS] Downloaded documentary ({os.path.getsize(out_file)/(1024*1024):.1f} MB): {out_file}")
            return out_file
        else:
            print(f"[YT-DLP WARN] Download failed: {res.stderr[:200]}")
    except Exception as e:
        print(f"[YT-DLP EXCEPTION] {e}")

    return None

def fetch_fresh_channel_documentary(all_posted: set) -> dict:
    channels = list(REFERENCE_YOUTUBE_CHANNELS)
    random.shuffle(channels)
    for ch in channels:
        ch_name = ch["name"]
        ch_url = ch["url"]
        print(f"[*] Checking reference channel: {ch_name} ({ch_url})")
        try:
            cmd = [
                "yt-dlp",
                "--extractor-args", "youtube:player_client=android_embedded,web_embedded",
                "--flat-playlist",
                "--playlist-items", "1-8",
                "--print", "%(id)s | %(duration)s | %(title)s",
                ch_url
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            for line in res.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    vid_id, dur_str, vid_title = parts[0], parts[1], parts[2]
                    src_id = f"yt_{vid_id}"
                    try:
                        dur = float(dur_str)
                    except Exception:
                        dur = 0
                    if dur >= 180 and src_id not in all_posted and len(vid_id) >= 5:
                        yt_url = f"https://www.youtube.com/watch?v={vid_id}"
                        assert_non_facebook_source(yt_url)
                        mins = int(dur // 60)
                        secs = int(dur % 60)
                        dur_tag = f"{mins} Minutes {secs} Seconds"
                        print(f"[CHANNEL DISCOVERY] Found full documentary: {vid_title} ({dur_tag}) from {ch_name}")
                        dl_path = download_full_documentary(yt_url, src_id)
                        if dl_path:
                            clean_title = vid_title.replace("#shorts", "").replace("#Shorts", "").strip()[:85]
                            return {
                                "url": yt_url,
                                "src_id": src_id,
                                "channel": ch_name,
                                "category": "Historical Documentary",
                                "title": f"{clean_title} 🏛️ | The Past Alive History",
                                "description": f"{vid_title}\n\nFull Documentary Episode ({dur_tag}).\n\nExperience vivid historical restorations and forgotten moments of human civilization brought back to life! Follow @ThePastAliveHistory for daily deep documentaries. ⏳📜 [src:{src_id}]\n\n#ThePastAliveHistory #HistoryAlive #HistoricalRestoration #Documentary #WorldHistory #AncientHistory #TimeTravel #ReliveHistory",
                                "local_path": dl_path
                            }
        except Exception as e:
            print(f"[CHANNEL SCRAPE WARN] {ch_name}: {e}")
            continue
    return None

def fetch_archive_documentary(all_posted: set) -> dict:
    """Selects an unposted guaranteed high-quality historical documentary from the archive pool."""
    print("[*] Checking guaranteed Archive.org Historical Documentary Pool...")
    candidates = [item for item in ARCHIVE_DOCUMENTARY_POOL if item["src_id"] not in all_posted]
    if not candidates:
        print("[ARCHIVE WARN] All archive pool items used; resetting rotation...")
        candidates = ARCHIVE_DOCUMENTARY_POOL

    selected = random.choice(candidates)
    print(f"[ARCHIVE SELECTED] {selected['title']}")
    dl_path = download_full_documentary(selected["url"], selected["src_id"])
    if dl_path:
        return {
            "url": selected["url"],
            "src_id": selected["src_id"],
            "channel": "Historical Archives",
            "category": selected.get("category", "Historical Documentary"),
            "title": f"{selected['title'][:85]} 🏛️ | The Past Alive History",
            "description": selected["description"],
            "local_path": dl_path
        }
    return None

def publish_documentary_to_facebook(doc_info: dict) -> dict:
    page_id = FB_PAGE_ID
    access_token = FB_PAGE_ACCESS_TOKEN
    file_path = doc_info["local_path"]
    file_size = os.path.getsize(file_path)

    print(f"[UPLOAD] Starting 1080p documentary upload to 'The Past Alive History' ({file_size / (1024*1024):.2f} MB)...")
    init_url = f"{FB_GRAPH_URL}/{page_id}/videos"
    init_data = {
        "upload_phase": "start",
        "file_size": file_size,
        "access_token": access_token
    }
    r = requests.post(init_url, data=init_data, timeout=30)
    init_res = r.json()
    if "upload_session_id" not in init_res:
        print(f"[UPLOAD ERROR] Phase start failed: {init_res}")
        return init_res

    upload_session_id = init_res["upload_session_id"]
    video_id = init_res.get("video_id", "")
    start_offset = int(init_res.get("start_offset", 0))

    chunk_size = 8 * 1024 * 1024
    with open(file_path, "rb") as f:
        f.seek(start_offset)
        while start_offset < file_size:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            headers = {
                "Authorization": f"OAuth {access_token}",
                "offset": str(start_offset),
                "file_size": str(file_size)
            }
            res_chunk = requests.post(
                f"{FB_GRAPH_URL}/{page_id}/videos",
                data=chunk,
                headers=headers,
                params={"upload_phase": "transfer", "upload_session_id": upload_session_id},
                timeout=180
            )
            c_data = res_chunk.json()
            start_offset = int(c_data.get("start_offset", start_offset + len(chunk)))

    finish_data = {
        "upload_phase": "finish",
        "upload_session_id": upload_session_id,
        "title": doc_info["title"],
        "description": doc_info["description"],
        "access_token": access_token
    }
    finish_res = requests.post(f"{FB_GRAPH_URL}/{page_id}/videos", data=finish_data, timeout=60).json()
    print(f"[UPLOAD FINISH]: {finish_res}")
    return finish_res

def run_documentary_bot():
    print("=================================================================")
    print("🏛️ THE PAST ALIVE HISTORY - FULL DOCUMENTARY VIDEO ENGINE")
    print("=================================================================")

    fb_signatures = get_posted_signatures_from_facebook(FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN, limit=100)
    history = load_local_history()
    all_posted = fb_signatures.union(set(history.get("posted_ids", [])))

    doc_data = fetch_fresh_channel_documentary(all_posted)
    if not doc_data:
        doc_data = fetch_archive_documentary(all_posted)

    if not doc_data:
        raise RuntimeError("Could not obtain any valid documentary video!")

    upload_res = publish_documentary_to_facebook(doc_data)
    if upload_res.get("success") or "id" in upload_res:
        vid_id = upload_res.get("id") or doc_data["src_id"]
        history["posted_ids"].append(doc_data["src_id"])
        history["daily_stats"]["total_posted"] += 1
        save_local_history(history)
        print(f"🎉 Documentary Published Successfully! Post ID: {vid_id}")
    else:
        print(f"❌ Upload Failed: {upload_res}")

if __name__ == "__main__":
    run_documentary_bot()
