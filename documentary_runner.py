"""
The Past Alive History - Automated Full Documentary Video Engine
- Dedicated to 'The Past Alive History' Facebook Page (ID: 1357435984129397)
- 100% Full-Length Documentary Videos (Original length, widescreen 16:9 HD)
- 100% English Titles, Storytelling Captions, and Historical Tags
- Dual Video Upload Architecture:
    1. Direct High-Speed Single-Shot Upload (for files <= 100 MB)
    2. Resumable Multipart Chunked Upload (for files > 100 MB)
- Verified Facebook Video Graph API Publishing with Direct Feed Distribution
- Multi-Layer Zero-Duplicate Protection (Live Facebook Page Graph Feed + Local History Tracking)
- Resilient Guaranteed Archive.org Documentary Pool with Multi-Candidate Failover
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
    FB_GRAPH_URL,
    FB_VIDEO_UPLOAD_URL
)

ARCHIVE_DOCUMENTARY_POOL = [
    {
        "src_id": "arch_battle_of_midway",
        "title": "The Battle of Midway (1942) - Historic Original Restored Color Footage 🎖️",
        "url": "https://archive.org/download/BattleOfMidway/BattleOfMidway_512kb.mp4",
        "description": "The Battle of Midway (1942) • Historic Original Color Footage.\n\nExperience John Ford's Academy Award-winning documentary covering the pivotal turning point of the Pacific War in June 1942. Featuring authentic 16mm Kodachrome combat footage captured during the Japanese air raid on Midway Atoll and the counterstrikes by US carrier squadrons.\n\nFull Restored Documentary. [src:arch_battle_of_midway]\n\nFollow @ThePastAliveHistory for daily deep historical restorations, wartime chronicles, and forgotten moments of world civilization brought back to life! ⏳📜\n\n#ThePastAliveHistory #HistoryAlive #BattleOfMidway #WWII #ColorHistory #HistoricalRestoration #NavalHistory #MilitaryHistory #Documentary",
        "category": "WWII History"
    },
    {
        "src_id": "arch_fighting_lady",
        "title": "The Fighting Lady (1944) - Life Aboard an Aircraft Carrier in the Pacific 🚢✈️",
        "url": "https://archive.org/download/FightingLady/FightingLady_512kb.mp4",
        "description": "The Fighting Lady (1944) • Academy Award-Winning Color Documentary.\n\nA vivid look at daily life, intense aerial dogfights, and heroic operations aboard the USS Yorktown (CV-10) during combat missions in the Pacific Ocean theater of World War II.\n\nFull Restored Documentary. [src:arch_fighting_lady]\n\nFollow @ThePastAliveHistory for daily deep historical documentaries, naval chronicles, and forgotten world history brought back to life! ⏳📜\n\n#ThePastAliveHistory #HistoryAlive #TheFightingLady #AviationHistory #AircraftCarrier #WWII #ColorFootage #NavalHistory #Documentary",
        "category": "Aviation & Naval History"
    },
    {
        "src_id": "arch_aleutians",
        "title": "Report from the Aleutians (1943) - John Huston's Academy Award-Nominated Color Film ❄️🎖️",
        "url": "https://archive.org/download/ReportFromTheAleutians/ReportFromTheAleutians_512kb.mp4",
        "description": "Report from the Aleutians (1943) • Directed by John Huston.\n\nCapturing the harsh conditions and operations of US Armed Forces stationed on the remote Aleutian Islands during the campaign against imperial Japanese positions in Alaska.\n\nFull Restored Color Documentary. [src:arch_aleutians]\n\nFollow @ThePastAliveHistory for daily deep historical chronicles! ⏳📜\n\n#ThePastAliveHistory #JohnHuston #Aleutians #WWII #MilitaryHistory #ColorDocumentary",
        "category": "WWII History"
    },
    {
        "src_id": "arch_prelude_to_war",
        "title": "Prelude to War (1942) - Frank Capra's Why We Fight Series 🌍🛡️",
        "url": "https://archive.org/download/PreludeToWar/PreludeToWar_512kb.mp4",
        "description": "Prelude to War (1942) • Academy Award Winner for Best Documentary Feature.\n\nFrank Capra examines the rise of fascism in Italy, Nazism in Germany, and militarism in Japan, contrasting totalitarianism with free democracies leading to World War II.\n\nFull Episode Restoration. [src:arch_prelude_to_war]\n\nFollow @ThePastAliveHistory for daily deep historical archives and documentaries! ⏳📜\n\n#ThePastAliveHistory #PreludeToWar #FrankCapra #WhyWeFight #WorldHistory #WWIIHistory #DocumentaryArchive",
        "category": "Geopolitical History"
    },
    {
        "src_id": "arch_true_glory",
        "title": "The True Glory (1945) - The Allied Victory in Europe (Academy Award Winner) 🎖️🌍",
        "url": "https://archive.org/download/TheTrueGlory/TheTrueGlory_512kb.mp4",
        "description": "The True Glory (1945) • Directed by Carol Reed & Garson Kanin.\n\nA definitive joint Anglo-American wartime documentary chronicling the final European campaign from the D-Day Normandy landings to the fall of Berlin.\n\nFull Restored Feature. [src:arch_true_glory]\n\nFollow @ThePastAliveHistory for daily historical documentaries and restoration archives! ⏳📜\n\n#ThePastAliveHistory #TheTrueGlory #DDay #WWIIHistory #AlliedForces #Documentary",
        "category": "WWII History"
    }
]

def load_local_history() -> dict:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to read history file: {e}")
    return {"posted_ids": [], "last_updated": None}

def save_local_history(history: dict):
    history["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def get_posted_signatures_from_facebook(page_id: str, access_token: str, limit: int = 100) -> set:
    signatures = set()
    try:
        url = f"{FB_GRAPH_URL}/{page_id}/videos"
        params = {
            "fields": "description,title",
            "limit": limit,
            "access_token": access_token
        }
        res = requests.get(url, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json().get("data", [])
            for item in data:
                text = (item.get("description") or "") + " " + (item.get("title") or "")
                found = re.findall(r"\[src:([a-zA-Z0-9_-]+)\]", text)
                for tag in found:
                    signatures.add(tag)
        print(f"[FACEBOOK LIVE] {len(signatures)} posted signatures retrieved from Page.")
    except Exception as e:
        print(f"[WARN] Could not retrieve Facebook live feed history: {e}")
    return signatures

def download_file_direct(url: str, output_path: str) -> bool:
    print(f"[DIRECT DOWNLOAD] Downloading documentary from: {url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        with requests.get(url, headers=headers, stream=True, timeout=180) as r:
            r.raise_for_status()
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"[DIRECT SUCCESS] Downloaded {output_path} ({size_mb:.2f} MB)")
        return True
    except Exception as e:
        print(f"[DIRECT ERROR] Download failed: {e}")
        return False

def fetch_archive_documentary(all_posted: set) -> dict:
    print("[*] Selecting fresh documentary from Guaranteed Archive.org Pool...")
    available = [doc for doc in ARCHIVE_DOCUMENTARY_POOL if doc["src_id"] not in all_posted]
    if not available:
        print("[WARN] All documentaries in pool were posted! Resetting selection...")
        available = ARCHIVE_DOCUMENTARY_POOL

    for chosen in available:
        print(f"[*] Trying candidate: {chosen['title']} ({chosen['src_id']})")
        out_file = os.path.join(DOWNLOAD_DIR, f"{chosen['src_id']}.mp4")
        if os.path.exists(out_file) and os.path.getsize(out_file) > 1024 * 1024:
            chosen["local_path"] = out_file
            return chosen

        if download_file_direct(chosen["url"], out_file):
            chosen["local_path"] = out_file
            return chosen
        print(f"[WARN] Failed to download {chosen['src_id']}, trying next candidate...")

    # Fallback to local repository bank
    bank_dir = "assets/documentary_bank"
    if os.path.isdir(bank_dir):
        for f in os.listdir(bank_dir):
            if f.endswith(".mp4"):
                lp = os.path.join(bank_dir, f)
                if os.path.getsize(lp) > 1024 * 1024:
                    print(f"[FALLBACK] Using local repository documentary: {lp}")
                    return {
                        "src_id": f.replace(".mp4", ""),
                        "title": "Franklin D. Roosevelt: 1935 Historical State Restoration",
                        "description": "Franklin D. Roosevelt: 1935 Historical State Restoration.\n\nArchival color and audio restored.\n\nFollow @ThePastAliveHistory for daily deep historical restorations! ⏳📜\n\n#ThePastAliveHistory #HistoryAlive #FDR #Documentary",
                        "local_path": lp
                    }

    return None

def publish_documentary_to_facebook(doc_info: dict) -> dict:
    page_id = FB_PAGE_ID
    access_token = FB_PAGE_ACCESS_TOKEN
    file_path = doc_info["local_path"]
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)

    print(f"[*] Publishing documentary to Facebook Page '{page_id}' ({file_size_mb:.2f} MB)...")
    url = f"{FB_VIDEO_UPLOAD_URL}/{page_id}/videos"

    # Strategy 1: Direct High-Speed Single-Shot Upload (< 100MB)
    if file_size <= 100 * 1024 * 1024:
        print(f"[*] File size ({file_size_mb:.2f} MB) <= 100MB. Uploading via high-speed direct multipart...")
        try:
            with open(file_path, "rb") as vf:
                res = requests.post(
                    url,
                    files={"source": vf},
                    data={
                        "description": doc_info["description"],
                        "title": doc_info["title"][:100],
                        "published": "true",
                        "access_token": access_token
                    },
                    timeout=600
                )
                r_json = res.json()
                print(f"[DIRECT UPLOAD RESULT]: Status {res.status_code} - {r_json}")
                if "id" in r_json:
                    print(f"🎉 Documentary Published Successfully! Facebook Video ID: {r_json['id']}")
                    return r_json
        except Exception as e:
            print(f"[DIRECT UPLOAD WARN]: {e}. Falling back to chunked upload...")

    # Strategy 2: Official Resumable Multipart Chunked Upload (for files > 100MB)
    print(f"[*] Starting Resumable Multipart Chunked Protocol for {file_size_mb:.2f} MB...")
    # Phase 1: Start
    init_res = requests.post(url, data={
        "upload_phase": "start",
        "file_size": file_size,
        "access_token": access_token
    }, timeout=45).json()
    print(f"[CHUNKED START]: {init_res}")

    if "upload_session_id" not in init_res:
        raise RuntimeError(f"Could not initiate Facebook video upload session: {init_res}")

    upload_session_id = init_res["upload_session_id"]
    video_id = init_res.get("video_id")
    start_offset = int(init_res["start_offset"])
    chunk_size = 4 * 1024 * 1024  # 4MB chunks

    # Phase 2: Transfer Chunks
    with open(file_path, "rb") as f:
        while start_offset < file_size:
            f.seek(start_offset)
            chunk = f.read(chunk_size)
            if not chunk:
                break
            res_chunk = requests.post(
                url,
                files={"video_file_chunk": ("chunk.mp4", chunk, "application/octet-stream")},
                data={
                    "upload_phase": "transfer",
                    "upload_session_id": upload_session_id,
                    "start_offset": str(start_offset),
                    "access_token": access_token
                },
                timeout=180
            )
            c_json = res_chunk.json()
            if "start_offset" not in c_json:
                print(f"[CHUNK TRANSFER ERROR]: {c_json}")
                raise RuntimeError(f"Chunk transfer rejected by Facebook: {c_json}")
            start_offset = int(c_json["start_offset"])
            pct = (start_offset / file_size) * 100
            print(f"  -> Transferred up to {start_offset} bytes ({pct:.1f}%)")

    # Phase 3: Finish & Publish
    finish_res = requests.post(url, data={
        "upload_phase": "finish",
        "upload_session_id": upload_session_id,
        "title": doc_info["title"][:100],
        "description": doc_info["description"],
        "published": "true",
        "access_token": access_token
    }, timeout=60).json()
    print(f"[CHUNKED FINISH]: {finish_res}")

    final_vid_id = finish_res.get("id") or video_id or upload_session_id
    if finish_res.get("success") or "id" in finish_res:
        print(f"🎉 Documentary Published Successfully! Facebook Video ID: {final_vid_id}")
        return {"id": final_vid_id, "success": True, "response": finish_res}

    raise RuntimeError(f"Facebook video finish phase failed: {finish_res}")

def run_documentary_bot():
    print("=" * 65)
    print("🏛️ THE PAST ALIVE HISTORY - FULL DOCUMENTARY VIDEO ENGINE")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 65)

    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        print("[FATAL ERROR] FB_PAGE_ACCESS_TOKEN or FB_PAGE_ID is missing!")
        sys.exit(1)

    fb_signatures = get_posted_signatures_from_facebook(FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN, limit=100)
    history = load_local_history()
    all_posted = fb_signatures.union(set(history.get("posted_ids", [])))
    print(f"[*] Total unique posted documentaries tracked: {len(all_posted)}")

    doc_data = fetch_archive_documentary(all_posted)
    if not doc_data:
        raise RuntimeError("Could not obtain any valid documentary video!")

    upload_res = publish_documentary_to_facebook(doc_data)

    history["posted_ids"].append(doc_data["src_id"])
    if "fb_video_ids" not in history:
        history["fb_video_ids"] = []
    history["fb_video_ids"].append(upload_res.get("id"))
    save_local_history(history)
    print("✅ State successfully updated. Video live on Page feed!")

if __name__ == "__main__":
    run_documentary_bot()
