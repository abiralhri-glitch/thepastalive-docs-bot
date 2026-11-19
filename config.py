import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
WATERMARK_PNG = os.path.join(ASSETS_DIR, "watermark_pastalive.png")
HISTORY_FILE = os.path.join(BASE_DIR, "posted_history.json")

# Facebook Page Credentials
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "61596668402545")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
FB_GRAPH_URL = "https://graph.facebook.com/v21.0"
