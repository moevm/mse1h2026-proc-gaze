import os
from pathlib import Path


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")
TRACKER_DIR = Path(os.environ.get("TRACKER_DIR"))
if not TRACKER_DIR.exists():
    raise ValueError("TRACKER_DIR environment variable is not set or path is bad")
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR"))
if not UPLOAD_DIR.exists():
    raise ValueError("UPLOAD_DIR environment variable is not set or path is bad")