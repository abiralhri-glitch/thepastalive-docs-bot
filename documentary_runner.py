"""
The Past Alive History - Automated Documentary & Historical Restoration Video Bot
- Dedicated to 'The Past Alive History' Facebook Page
- 100% Full Original Video (No forced blur cropping, native resolution & aspect ratio preserved)
- 100% English Titles, Captions, and Descriptions
- Sleek Official Corner Watermark Badge
- Broadcast-grade Loudnorm Audio Normalization
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
import imageio_ffmpeg

from config import (
    BASE_DIR,
    DOWNLOAD_DIR,
    OUTPUT_DIR,
    WATERMARK_BADGE_PNG,
    HISTORY_FILE,
    FB_PAGE_ID,
    FB_PAGE_ACCESS_TOKEN,
    FB_GRAPH_URL
)
from documentary_sources import REFERENCE_YOUTUBE_CHANNELS, DYNAMIC_SEARCH_QUERIES
from curated_seeds import OFFLINE_DOCUMENTARY_SEEDS

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

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

def download_youtube_video(url: str, src_id: str) -> str:
    """Download video from YouTube using yt-dlp."""
    assert_non_facebook_source(url)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    out_file = os.path.join(DOWNLOAD_DIR, f"{src_id}.mp4")
    
    if os.path.exists(out_file) and os.path.getsize(out_file) > 100000:
        return out_file

    cmd = [
        "yt-dlp",
        "--extractor-args", "youtube:player_client=ios,web",
        "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "--merge-output-format", "mp4",
        "-o", out_file,
        url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(out_file) and os.path.getsize(out_file) > 100000:
        return out_file
    print(f"[YT-DLP WARN] Download failed: {res.stderr[:200]}")
    return None

def fetch_fresh_channel_video(all_posted: set) -> dict:
    """Scrape fresh documentary videos from the 17 reference YouTube channels."""
    channels = list(REFERENCE_YOUTUBE_CHANNELS)
    random.shuffle(channels)
    
    for ch in channels:
        ch_url = ch.get("url")
        ch_name = ch.get("name")
        print(f"[*] Checking channel: {ch_name} ({ch_url})")
        try:
            cmd = [
                "yt-dlp",
                "--extractor-args", "youtube:player_client=ios,web",
                "--flat-playlist",
                "-I", "1:10",
                "--print", "%(id)s | %(title)s | %(duration)s",
                ch_url
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            for line in res.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 2:
                    vid_id, vid_title = parts[0], parts[1]
                    src_id = f"yt_{vid_id}"
                    if src_id not in all_posted and len(vid_id) >= 5:
                        yt_url = f"https://www.youtube.com/watch?v={vid_id}"
                        assert_non_facebook_source(yt_url)
                        print(f"[CHANNEL DISCOVERY] Found documentary: {vid_title} from {ch_name}")
                        dl_path = download_youtube_video(yt_url, src_id)
                        if dl_path:
                            clean_title = vid_title.replace("#shorts", "").replace("#Shorts", "").strip()[:80]
                            return {
                                "url": yt_url,
                                "src_id": src_id,
                                "channel": ch_name,
                                "category": "Historical Restoration",
                                "title": f"🏛️ {clean_title} | The Past Alive History",
                                "description": f"{clean_title}\n\nExperience vivid historical restorations and forgotten moments of human civilization brought back to life! Follow @ThePastAliveHistory for daily deep documentaries. ⏳📜 [src:{src_id}]\n\n#ThePastAliveHistory #HistoryAlive #HistoricalRestoration #Documentary #WorldHistory #AncientHistory #TimeTravel #ReliveHistory",
                                "local_path": dl_path
                            }
        except Exception as e:
            print(f"[CHANNEL SCRAPE WARN] {ch_name}: {e}")
            continue
    return None

def apply_full_video_branding(input_video_path: str, output_path: str) -> str:
    """
    Renders the video in its FULL original aspect ratio and resolution:
    - 100% full original video (no cropping, no forced blur bars, native resolution preserved)
    - Pristine H.264 / AAC encoding with broadcast loudnorm audio
    - Clean official branding watermark placed dynamically in top-right corner
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    filter_complex = (
        "[0:v][1:v]overlay=W-w-30:30[v_final];"
        "[0:a]volume=1.05,loudnorm=I=-16:TP=-1.5:LRA=11[a_final]"
    )

    cmd = [
        FFMPEG_EXE, "-y",
        "-i", input_video_path,
        "-i", WATERMARK_BADGE_PNG,
        "-filter_complex", filter_complex,
        "-map", "[v_final]",
        "-map", "[a_final]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-b:v", "6000k", "-maxrate", "8000k", "-bufsize", "12000k",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
        "-map_metadata", "-1",
        output_path
    ]

    subprocess.run(cmd, check=True)
    return output_path

def publish_video_to_facebook(video_path: str, title: str, description: str, page_id: str, access_token: str) -> dict:
    """
    Publishes full video directly to Facebook Page Feed & Watch via Graph API Videos endpoint.
    Supports all aspect ratios (16:9 widescreen, 9:16 vertical, 1:1 square) in full original glory.
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
            timeout=180
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

    # Step 2: Content Selection (100% English titles & captions)
    target_item = None

    # Priority A: Curated Repository Video Bank
    for seed in OFFLINE_DOCUMENTARY_SEEDS:
        src_id = seed["src_id"]
        local_f = os.path.join(seed["dir"], seed["file"])
        if src_id not in all_posted and os.path.exists(local_f) and os.path.getsize(local_f) > 50000:
            print(f"[SELECTION] Selecting curated repository documentary: {seed['title']}")
            target_item = seed.copy()
            target_item["local_path"] = local_f
            break

    # Priority B: Reference Channels Dynamic Scraper
    if not target_item:
        print("[*] Checking 17 reference YouTube channels for fresh documentaries...")
        target_item = fetch_fresh_channel_video(all_posted)

    # Priority C: Recycling unposted repository seed if all published
    if not target_item:
        print("[*] Rotating through available repository documentaries...")
        for seed in OFFLINE_DOCUMENTARY_SEEDS:
            local_f = os.path.join(seed["dir"], seed["file"])
            if os.path.exists(local_f) and os.path.getsize(local_f) > 50000:
                target_item = seed.copy()
                target_item["local_path"] = local_f
                break

    if not target_item:
        print("[ERROR] Could not find any valid documentary video!")
        sys.exit(1)

    print(f"[*] Target video ready: {target_item['title']} (src: {target_item['src_id']})")

    # Step 3: Full Video Rendering & Watermarking (100% Full Video, Original Aspect Ratio)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    final_output = os.path.join(OUTPUT_DIR, f"final_{target_item['src_id']}.mp4")
    
    print("[*] Applying Full Video Branding (Preserving original aspect ratio & full video)...")
    apply_full_video_branding(target_item["local_path"], final_output)
    print(f"[+] Render complete: {final_output} ({os.path.getsize(final_output) / (1024 * 1024):.2f} MB)")

    # Step 4: Publish Full Video to Facebook Page
    print("[*] Publishing Full Video to Facebook Page 'The Past Alive History'...")
    fb_res = publish_video_to_facebook(
        video_path=final_output,
        title=target_item["title"],
        description=target_item["description"],
        page_id=FB_PAGE_ID,
        access_token=FB_PAGE_ACCESS_TOKEN
    )
    print(f"[+] Facebook Response: {json.dumps(fb_res)}")

    # Step 5: Update History
    history["posted_ids"].append(target_item["src_id"])
    history["daily_stats"]["total_posted"] = history["daily_stats"].get("total_posted", 0) + 1
    save_local_history(history)
    print(f"✅ Successfully posted full video '{target_item['title']}'! Daily total: {history['daily_stats']['total_posted']}")

if __name__ == "__main__":
    run_documentary_bot()
