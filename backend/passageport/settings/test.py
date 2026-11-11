import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
os.environ.setdefault("DJANGO_SECRET_KEY", "passageport-test-only-key-" * 4)

from .base import *  # noqa: E402,F403

ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa: F405
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
