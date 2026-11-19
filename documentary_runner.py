"""
The Past Alive History - Automated Documentary & Historical Restoration Reel Bot
- Dedicated to 'The Past Alive History' Facebook Page
- 100% Non-Facebook Sources (Curated YouTube Shorts & 17 Reference Channels)
- Smart Dual-Layer 1080x1920 Framing (Cinematic Background Blur + Uncropped Center)
- Crystal-Clear Official Branding Watermark
- Audio Loudnorm Normalization (Broadcast Standard)
- Multi-Layer Zero-Duplicate Protection (Facebook Live Feed Verification + Signature Tracking)
- Runs 3 Times Daily on GitHub Actions (06:00 PM, 09:00 PM, 03:00 AM BDT)
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
    WATERMARK_PNG,
    HISTORY_FILE,
    FB_PAGE_ID,
    FB_PAGE_ACCESS_TOKEN,
    FB_GRAPH_URL
)
from documentary_sources import REFERENCE_YOUTUBE_CHANNELS, DYNAMIC_SEARCH_QUERIES
from curated_seeds import CURATED_DOCUMENTARY_SEEDS

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
        "--extractor-args", "youtube:player_client=android",
        "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "--merge-output-format", "mp4",
        "-o", out_file,
        url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(out_file) and os.path.getsize(out_file) > 100000:
        return out_file
    print(f"[YT-DLP WARN] Download failed: {res.stderr[:300]}")
    return None

def fetch_fresh_channel_video(all_posted: set) -> dict:
    """Scrape fresh shorts from the 17 reference YouTube channels."""
    channels = list(REFERENCE_YOUTUBE_CHANNELS)
    random.shuffle(channels)
    
    for ch in channels:
        ch_url = ch.get("url")
        ch_name = ch.get("name")
        print(f"[*] Checking channel: {ch_name} ({ch_url})")
        try:
            cmd = [
                "yt-dlp",
                "--extractor-args", "youtube:player_client=android",
                "--flat-playlist",
                "-I", "1:15",
                "--print", "%(id)s | %(title)s | %(duration)s",
                ch_url
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            for line in res.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 2:
                    vid_id, vid_title = parts[0], parts[1]
                    src_id = f"yt_{vid_id}"
                    if src_id not in all_posted and len(vid_id) >= 5:
                        yt_url = f"https://www.youtube.com/watch?v={vid_id}"
                        assert_non_facebook_source(yt_url)
                        print(f"[CHANNEL DISCOVERY] Found new documentary video: {vid_title} from {ch_name}")
                        dl_path = download_youtube_video(yt_url, src_id)
                        if dl_path:
                            clean_title = vid_title.replace("#shorts", "").replace("#Shorts", "").strip()[:65]
                            return {
                                "url": yt_url,
                                "src_id": src_id,
                                "channel": ch_name,
                                "category": "Historical Restoration",
                                "title": f"🏛️ {clean_title} ✨ | দ্য পাস্ট অ্যালাইভ হিস্ট্রি",
                                "description": f"{vid_title}\n\nইতিহাসের বিস্ময়কর মুহূর্ত ও জীবন্ত অতীত দেখতে পেজটি ফলো করে সাথেই থাকুন! ⏳📜 [src:{src_id}]\n\n#ThePastAliveHistory #HistoryAlive #HistoricalRestoration #DocumentaryReels #WorldHistory #AncientHistory #ReliveHistory",
                                "local_path": dl_path
                            }
        except Exception as e:
            print(f"[CHANNEL SCRAPE WARN] {ch_name}: {e}")
            continue
    return None

def fetch_fresh_search_video(all_posted: set) -> dict:
    """Fallback search across historical documentary queries."""
    queries = list(DYNAMIC_SEARCH_QUERIES)
    random.shuffle(queries)
    for q in queries:
        try:
            cmd = [
                "yt-dlp",
                "--extractor-args", "youtube:player_client=android",
                f"ytsearch10:{q}",
                "--print", "%(id)s | %(title)s | %(duration)s",
                "--no-playlist"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            for line in res.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 2:
                    vid_id, vid_title = parts[0], parts[1]
                    src_id = f"yt_{vid_id}"
                    if src_id not in all_posted and len(vid_id) >= 5:
                        yt_url = f"https://www.youtube.com/watch?v={vid_id}"
                        assert_non_facebook_source(yt_url)
                        print(f"[SEARCH DISCOVERY] Found documentary reel: {vid_title}")
                        dl_path = download_youtube_video(yt_url, src_id)
                        if dl_path:
                            clean_title = vid_title.replace("#shorts", "").replace("#Shorts", "").strip()[:65]
                            return {
                                "url": yt_url,
                                "src_id": src_id,
                                "channel": "Historical Archives",
                                "category": "Documentary",
                                "title": f"📜 {clean_title} ⏳ | দ্য পাস্ট অ্যালাইভ হিস্ট্রি",
                                "description": f"{vid_title}\n\nঅতীতের হারিয়ে যাওয়া সভ্যতা ও রোমাঞ্চকর ইতিহাস। [src:{src_id}]\n\n#ThePastAliveHistory #DeepHistory #HistoricalDocumentary #TimeTravel #LostWonders",
                                "local_path": dl_path
                            }
        except Exception as e:
            print(f"[SEARCH SCRAPE WARN] {q}: {e}")
            continue
    return None

def apply_smart_dual_layer_framing(input_video_path: str, output_path: str) -> str:
    """
    Apply Smart Dual-Layer 1080x1920 Framing:
    - Zero cropping: Center video retains 100% original aspect ratio and subtitles.
    - Blurred background: Scales and crops to fill 1080x1920 with cinematic gaussian blur.
    - Official watermark overlay.
    - Loudnorm audio normalization.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:3,setsar=1[bg];"
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,setsar=1[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[v_base];"
        "[v_base][1:v]overlay=0:0[v_final];"
        "[0:a]volume=1.1,loudnorm=I=-16:TP=-1.5:LRA=11[a_final]"
    )

    cmd = [
        FFMPEG_EXE, "-y",
        "-i", input_video_path,
        "-i", WATERMARK_PNG,
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
    """Upload video to Facebook Page Reels with Feed API fallback."""
    file_size = os.path.getsize(video_path)
    print(f"[*] Uploading to Facebook Page: {video_path} ({file_size / (1024 * 1024):.2f} MB)")

    # Phase 1: Initialize session
    init_url = f"{FB_GRAPH_URL}/{page_id}/video_reels"
    init_res = requests.post(init_url, data={"upload_phase": "start", "access_token": access_token}, timeout=30)
    init_data = init_res.json()

    if "video_id" not in init_data:
        print("[!] Reels API failed, using standard Videos Feed endpoint...")
        url = f"{FB_GRAPH_URL}/{page_id}/videos"
        with open(video_path, "rb") as f:
            res = requests.post(
                url,
                files={"source": f},
                data={"description": description, "title": title, "access_token": access_token},
                timeout=120
            )
            return res.json()

    video_id = init_data["video_id"]
    upload_url = init_data.get("upload_url")

    # Phase 2: Binary transfer
    with open(video_path, "rb") as f:
        headers = {
            "Authorization": f"OAuth {access_token}",
            "offset": "0",
            "file_size": str(file_size)
        }
        requests.post(upload_url, headers=headers, data=f, timeout=120)

    # Phase 3: Publish
    pub_url = f"{FB_GRAPH_URL}/{page_id}/video_reels"
    pub_data = {
        "upload_phase": "finish",
        "access_token": access_token,
        "video_id": video_id,
        "video_state": "PUBLISHED",
        "description": description,
        "title": title
    }
    pub_res = requests.post(pub_url, data=pub_data, timeout=30)
    return pub_res.json()

def run_documentary_bot():
    print("=" * 65)
    print("🚀 THE PAST ALIVE HISTORY - AUTOMATED DOCUMENTARY POSTING BOT")
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

    # Step 2: Content Selection
    target_item = None

    # Priority A: Curated Seeds
    for seed in CURATED_DOCUMENTARY_SEEDS:
        if seed["src_id"] not in all_posted:
            print(f"[SELECTION] Selecting curated seed: {seed['title']}")
            dl_path = download_youtube_video(seed["url"], seed["src_id"])
            if dl_path:
                target_item = seed.copy()
                target_item["local_path"] = dl_path
                break

    # Priority B: Reference Channels Scraper
    if not target_item:
        print("[*] Checking 17 reference YouTube channels for fresh shorts...")
        target_item = fetch_fresh_channel_video(all_posted)

    # Priority C: Dynamic Query Search
    if not target_item:
        print("[*] Fallback: Searching historical documentary queries...")
        target_item = fetch_fresh_search_video(all_posted)

    if not target_item:
        print("[ERROR] Could not find any fresh unposted documentary video!")
        sys.exit(1)

    print(f"[*] Target video ready: {target_item['title']} (src: {target_item['src_id']})")

    # Step 3: Video Framing & Watermarking
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    final_output = os.path.join(OUTPUT_DIR, f"final_{target_item['src_id']}.mp4")
    
    print("[*] Applying 1080x1920 Smart Dual-Layer Framing & Watermarking...")
    apply_smart_dual_layer_framing(target_item["local_path"], final_output)
    print(f"[+] Render complete: {final_output} ({os.path.getsize(final_output) / (1024 * 1024):.2f} MB)")

    # Step 4: Publish to Facebook Page
    print("[*] Publishing to Facebook Page 'The Past Alive History'...")
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
    print(f"✅ Successfully posted '{target_item['title']}'! Daily total: {history['daily_stats']['total_posted']}")

if __name__ == "__main__":
    run_documentary_bot()
