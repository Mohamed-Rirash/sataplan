from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()


SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
FRONTEND_URL = os.getenv("QR_CODE_URL")
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS")
DATABASE_URL = os.getenv("DATABASE_URL")
URL = os.getenv("URL")
KEY = os.getenv("KEY")
BUCKET = os.getenv("BUCKET")


def get_cors_origins():
    """
    Parse CORS origins from environment variable.
    Supports comma-separated list of origins.
    """
    cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
    # Add localhost for development if not already present
    if "http://localhost:5173" not in cors_origins:
        cors_origins.append("http://localhost:5173")

    # Remove any empty strings
    return [origin.strip() for origin in cors_origins if origin.strip()]


supabase: Client = create_client(URL, KEY)
