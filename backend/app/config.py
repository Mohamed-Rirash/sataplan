from dotenv import load_dotenv
import os

load_dotenv()


SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
FRONTEND_URL = os.getenv("QR_CODE_URL")
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS")
DATABASE_URL = os.getenv("DATABASE_URL")
