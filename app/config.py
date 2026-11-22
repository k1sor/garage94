import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "change-me"
    DEBUG = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")

    # Supabase (PostgreSQL) in deploy, SQLite for local development and tests.
    _db_url = os.getenv("DATABASE_URL", "sqlite:///garage_vinyl.db").strip()
    if _db_url.startswith("postgres://"):
        _db_url = "postgresql://" + _db_url[len("postgres://"):]
    if _db_url.startswith("sqlite:///"):
        path = _db_url.replace("sqlite:///", "", 1)
        if not os.path.isabs(path):
            _db_url = f"sqlite:///{BASE_DIR / path}"
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    if _db_url.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "media")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB
    WTF_CSRF_ENABLED = True

    SITE_URL = os.getenv("SITE_URL", "https://example.com").rstrip("/")
    SEND_FILE_MAX_AGE_DEFAULT = 60 * 60 * 24 * 30
