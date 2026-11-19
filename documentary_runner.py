"""
The Past Alive History - Automated Full Documentary Video Bot
- Dedicated to 'The Past Alive History' Facebook Page
- 100% Full Long-Form Documentary Videos (Original length, however many minutes long)
- 100% English Titles, Storytelling Captions, and Tags
- Native 16:9 Full Widescreen Format (Zero cropping, zero blur borders)
- Multi-Layer Zero-Duplicate Protection (Live Facebook Graph API Feed Verification)
- 3 Daily Upload Slots on GitHub Actions (06:00 PM, 09:00 PM, 03:00 AM BDT)
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
    """Download full documentary video from YouTube using yt-dlp."""
    assert_non_facebook_source(url)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    out_file = os.path.join(DOWNLOAD_DIR, f"{src_id}.mp4")
    
    if os.path.exists(out_file) and os.path.getsize(out_file) > 1000000:
        return out_file

    cmd = [
        "yt-dlp",
        "--extractor-args", "youtube:player_client=ios,web",
        "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
        "--merge-output-format", "mp4",
        "-o", out_file,
        url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(out_file) and os.path.getsize(out_file) > 1000000:
        return out_file
    print(f"[YT-DLP WARN] Download failed: {res.stderr[:200]}")
    return None

def fetch_fresh_channel_documentary(all_posted: set) -> dict:
    """Scrape fresh full-length documentary videos from the 17 reference YouTube channels."""
    channels = list(REFERENCE_YOUTUBE_CHANNELS)
    random.shuffle(channels)
    
    for ch in channels:
        ch_url = ch.get("url")
        ch_name = ch.get("name")
        print(f"[*] Checking reference channel: {ch_name} ({ch_url})")
        try:
            # Query recent full videos from channel (duration >= 180s)
            cmd = [
                "yt-dlp",
                "--extractor-args", "youtube:player_client=ios,web",
                "--flat-playlist",
                "-I", "1:8",
                "--print", "%(id)s | %(duration)s | %(title)s",
                ch_url
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            for line in res.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    vid_id, dur_str, vid_title = parts[0], parts[1], parts[2]
                    src_id = f"yt_{vid_id}"
                    
                    try:
                        dur = float(dur_str)
                    except Exception:
                        dur = 0
                    
                    # Ensure it is a FULL documentary video (at least 3 minutes, not a short)
                    if dur >= 180 and src_id not in all_posted and len(vid_id) >= 5:
                        yt_url = f"https://www.youtube.com/watch?v={vid_id}"
                        assert_non_facebook_source(yt_url)
                        
                        mins = int(dur // 60)
                        secs = int(dur % 60)
                        dur_tag = f"{mins} Minutes {secs} Seconds" if mins > 0 else f"{int(dur)} Seconds"
                        
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

def fetch_fresh_search_documentary(all_posted: set) -> dict:
    """Fallback search across historical documentary queries for full-length episodes."""
    queries = list(DYNAMIC_SEARCH_QUERIES)
    random.shuffle(queries)
    for q in queries:
        try:
            cmd = [
                "yt-dlp",
                "--extractor-args", "youtube:player_client=ios,web",
                f"ytsearch8:{q}",
                "--print", "%(id)s | %(duration)s | %(title)s",
                "--no-playlist"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
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
                        
                        print(f"[SEARCH DISCOVERY] Found full documentary: {vid_title} ({dur_tag})")
                        dl_path = download_full_documentary(yt_url, src_id)
                        if dl_path:
                            clean_title = vid_title.replace("#shorts", "").replace("#Shorts", "").strip()[:85]
                            return {
                                "url": yt_url,
                                "src_id": src_id,
                                "channel": "Historical Archives",
                                "category": "Documentary",
                                "title": f"{clean_title} ⏳ | The Past Alive History",
                                "description": f"{vid_title}\n\nFull Documentary Episode ({dur_tag}).\n\nLost civilizations, ancient architectural marvels, and breathtaking moments of history. [src:{src_id}]\n\n#ThePastAliveHistory #DeepHistory #HistoricalDocumentary #TimeTravel #LostWonders",
                                "local_path": dl_path
                            }
        except Exception as e:
            print(f"[SEARCH SCRAPE WARN] {q}: {e}")
            continue
    return None

def publish_video_to_facebook(video_path: str, title: str, description: str, page_id: str, access_token: str) -> dict:
    """
    Publishes full-length video directly to Facebook Page Feed & Watch via Graph API Videos endpoint.
    Maintains full 16:9 widescreen resolution, complete length, and full video player experience.
    """
    file_size = os.path.getsize(video_path)
    print(f"[*] Publishing Full Video to Facebook Page: {video_path} ({file_size / (1024 * 1024):.2f} MB)")

    url = f"{FB_GRAPH_URL}/{page_id}/videos"
    with open(video_path, "rb") as f:
        res = requests.post(
            url,
            files={"source": f},
            data={
                "description": description,
                "title": title,
                "access_token": access_token
            },
            timeout=300
        )
        return res.json()

def run_documentary_bot():
    print("=" * 65)
    print("🚀 THE PAST ALIVE HISTORY - AUTOMATED FULL DOCUMENTARY VIDEO BOT")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 65)

    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        print("[FATAL ERROR] FB_PAGE_ACCESS_TOKEN or FB_PAGE_ID is missing!")
        sys.exit(1)

    # Step 1: Deduplication Check
    history = load_local_history()
    local_posted = set(history.get("posted_ids", []))
    fb_live_posted = get_posted_signatures_from_facebook(FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN)
    all_posted = local_posted.union(fb_live_posted)

    print(f"[*] Total unique posted videos tracked: {len(all_posted)}")

    # Step 2: Content Selection (Full long-form documentaries >= 3 minutes)
    target_item = fetch_fresh_channel_documentary(all_posted)

    if not target_item:
        print("[*] Fallback: Searching curated documentary queries...")
        target_item = fetch_fresh_search_documentary(all_posted)

    if not target_item:
        print("[ERROR] Could not find any valid full documentary video!")
        sys.exit(1)

    print(f"[*] Target documentary ready: {target_item['title']} (src: {target_item['src_id']})")

    # Step 3: Publish Full Video to Facebook Page (Full original video, full duration)
    print("[*] Publishing Full Video to Facebook Page 'The Past Alive History'...")
    fb_res = publish_video_to_facebook(
        video_path=target_item["local_path"],
        title=target_item["title"],
        description=target_item["description"],
        page_id=FB_PAGE_ID,
        access_token=FB_PAGE_ACCESS_TOKEN
    )
    print(f"[+] Facebook Response: {json.dumps(fb_res)}")

    # Step 4: Update History
    history["posted_ids"].append(target_item["src_id"])
    history["daily_stats"]["total_posted"] = history["daily_stats"].get("total_posted", 0) + 1
    save_local_history(history)
    print(f"✅ Successfully posted full documentary '{target_item['title']}'! Daily total: {history['daily_stats']['total_posted']}")

if __name__ == "__main__":
    run_documentary_bot()
