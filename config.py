import os
from pathlib import Path

from dotenv import load_dotenv

from constants import ConfigMessages


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def load_business_context():
    # Mevcut ortam değişkeni desteğini koruyoruz.
    context = os.environ.get("BUSINESS_CONTEXT")

    if context is None:
        prompt_path = (
            BASE_DIR
            / "app"
            / "prompts"
            / "reading_assistant.txt"
        )

        try:
            context = prompt_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise RuntimeError(
                f"Chatbot talimat dosyası okunamadı: {prompt_path}"
            ) from error

    if not context.strip():
        raise RuntimeError("Chatbot talimatı boş olamaz.")

    return context.strip()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        "smartlead.db",
    )

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

    AI_PROVIDER = os.environ.get("AI_PROVIDER", "groq")

    GROQ_MODEL = os.environ.get(
        "GROQ_MODEL",
        "openai/gpt-oss-20b",
    )

    BUSINESS_CONTEXT = load_business_context()

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.environ.get(
            "CORS_ORIGINS",
            "http://localhost:5000",
        ).split(",")
        if origin.strip()
    ]


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}