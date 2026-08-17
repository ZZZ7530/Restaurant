import os
import secrets

from dotenv import load_dotenv


load_dotenv()


def _get_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_secret_key(environment):
    secret_key = os.getenv("SECRET_KEY")
    weak_values = {
        "",
        "dev-secret-key",
        "change-this-secret-key",
        "secret",
        "changeme",
    }

    if secret_key and secret_key.strip() not in weak_values:
        return secret_key

    if environment == "production":
        raise RuntimeError("SECRET_KEY must be set to a strong value in production.")

    return secrets.token_urlsafe(32)


class Config:
    FLASK_ENV = os.getenv("FLASK_ENV", "production").strip().lower()
    IS_PRODUCTION = FLASK_ENV == "production"
    DEBUG = _get_bool("FLASK_DEBUG", default=FLASK_ENV == "development")
    SECRET_KEY = _get_secret_key(FLASK_ENV)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = _get_bool("SESSION_COOKIE_SECURE", default=IS_PRODUCTION)

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "traditional_restaurant")
    MYSQL_CHARSET = os.getenv("MYSQL_CHARSET", "utf8mb4")
    MYSQL_COLLATION = os.getenv("MYSQL_COLLATION", "utf8mb4_unicode_ci")
    MYSQL_URI = (
        f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@"
        f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        f"?charset={MYSQL_CHARSET}&collation={MYSQL_COLLATION}"
    )

    RESTAURANT_NAME = os.getenv("RESTAURANT_NAME", "上漁港活海產")
    TABLE_ORDER_BASE_URL = os.getenv("TABLE_ORDER_BASE_URL", "http://127.0.0.1:5000")
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
    LINE_USER_ID = os.getenv("LINE_USER_ID", "")
    LINE_GROUP_ID = os.getenv("LINE_GROUP_ID", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")
    OPENAI_API_BASE_URL = os.getenv("OPENAI_API_BASE_URL", "")
    AI_MOCK_MODE = os.getenv("AI_MOCK_MODE", "false").lower() == "true"
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads/menu")
