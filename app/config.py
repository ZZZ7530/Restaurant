import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DEBUG = os.getenv("FLASK_ENV", "production") == "development"

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
    LINE_USER_ID = os.getenv("LINE_USER_ID", "")
    LINE_GROUP_ID = os.getenv("LINE_GROUP_ID", "")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads/menu")
    # Development fallback only. In production, set ADMIN_USERNAME and ADMIN_PASSWORD in environment variables.
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
