"""Create local development secrets without overwriting an existing configuration."""

import os
import secrets
from pathlib import Path

env_path = Path(__file__).resolve().parents[1] / ".env"
password = secrets.token_urlsafe(32)
content = (
    f"DJANGO_SECRET_KEY={secrets.token_urlsafe(64)}\n"
    "DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,[::1]\n"
    "POSTGRES_DB=passageport\n"
    "POSTGRES_USER=passageport\n"
    f"POSTGRES_PASSWORD={password}\n"
    f"DATABASE_URL=postgresql://passageport:{password}@127.0.0.1:5433/passageport\n"
)
try:
    descriptor = os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    raise SystemExit(".env zaten var; mevcut ayarlar korundu.") from None
with os.fdopen(descriptor, "w") as env_file:
    env_file.write(content)
print("Yerel .env oluşturuldu. Gizli değerler ekrana yazdırılmadı.")
