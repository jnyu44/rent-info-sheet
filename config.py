"""Configuration for the Rent Info PDF tool."""
import os

# Google Sheets published CSV URL
# To get this URL: Open your Google Sheet -> File -> Share -> Publish to web -> Select CSV -> Publish
# Then paste the URL below.
SHEET_URL = os.environ.get(
    "SHEET_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vTaEPtBucDopC3jj1g7uCQ6mvfvFK8Q2VT8dpjjVMfAeJ5pATkXUG_vEkw1o5cZyyZmGYIReMOQgv5X/pub?gid=0&single=true&output=csv"
)

# Server settings
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5002))
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
