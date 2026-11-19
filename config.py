import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
WATERMARK_PNG = os.path.join(ASSETS_DIR, "watermark_pastalive.png")
WATERMARK_BADGE_PNG = os.path.join(ASSETS_DIR, "watermark_badge.png")
HISTORY_FILE = os.path.join(BASE_DIR, "posted_history.json")

# Facebook Page Credentials for 'The Past Alive History' (ID: 1357435984129397)
# Permanent Lifetime Page Access Token (Expires: 0 / Never Expires)
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") or "1357435984129397"
FB_PAGE_ACCESS_TOKEN = (
    os.environ.get("FB_PAGE_ACCESS_TOKEN")
    or "EAAe1H3izQCYBTJQBvOaHQEGJsBmuNHakictMzwEBAxwvaUOZAYMUZCCNSy4etPnEB2r0JNOZC3PcdVyO3opCPZCAK4LZBncYUEjm7gKN5oiZBpaoDgk6t12ZCg7ZCllwSCd1lkWnkNG3AtUMBfow044GWJF68B5xHmu7qVLpCANGOtnKYBNDRF2UmUz69etDV9NxR9JfZBPrQ"
)
FB_GRAPH_URL = "https://graph.facebook.com/v21.0"
FB_VIDEO_UPLOAD_URL = "https://graph-video.facebook.com/v21.0"
