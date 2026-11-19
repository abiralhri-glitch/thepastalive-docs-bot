import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
WATERMARK_PNG = os.path.join(ASSETS_DIR, "watermark_pastalive.png")
WATERMARK_BADGE_PNG = os.path.join(ASSETS_DIR, "watermark_badge.png")
HISTORY_FILE = os.path.join(BASE_DIR, "posted_history.json")

# Facebook Page Credentials for 'The Past Alive History'
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") or "1357435984129397"
FB_PAGE_ACCESS_TOKEN = (
    os.environ.get("FB_PAGE_ACCESS_TOKEN")
    or "EAAe1H3izQCYBTFBsFmilBN6vpz92Y9ZAZB6ZCDJpPtsHFkDy6V4DnsEXcEbjLYK1sdII4rlTNOjBWUQXpcMOTljh7ioCA5Nk46fvYAH10XywkKk0DUoYvwCa8UeDYcZAaeCORJYgChh3FPZCFbJw0U2AIuGtvhC2ebTdy6ovuYiEfwA6nDKDCZCbKY6yqOZBZBHKXtyhJnRZAiZBPH8itXEfwu2ZBsvZAhxIByPF4vbZBnjvC"
)
FB_GRAPH_URL = "https://graph.facebook.com/v21.0"
