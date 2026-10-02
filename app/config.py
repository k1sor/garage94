import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")

    # The college version uses SQLite only.
    _db_url = os.getenv("DATABASE_URL", "sqlite:///garage_vinyl.db").strip()
    if not _db_url.startswith("sqlite:///"):
        _db_url = "sqlite:///garage_vinyl.db"
    if not os.path.isabs(_db_url.replace("sqlite:///", "", 1)):
        _db_url = f"sqlite:///{BASE_DIR / _db_url.replace('sqlite:///', '', 1)}"
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "media")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB
    WTF_CSRF_ENABLED = True
