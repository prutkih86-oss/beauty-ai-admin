import os
import urllib3
from dotenv import load_dotenv

load_dotenv()

# Backend API base URL (без '/api' на кінці, щоб уникнути дублювання /api/api/)
API_BASE_URL = os.environ.get(
    "API_BASE_URL", "http://localhost:8000"
)

# Admin/staff account credentials for JWT auth (POST /api/users/token/)
API_EMAIL = os.environ.get("API_EMAIL")
API_PASSWORD = os.environ.get("API_PASSWORD")

# Опція для ігнорування помилок SSL (корисно під час використання самопідписаних сертифікатів)
VERIFY_SSL = os.environ.get("VERIFY_SSL", "false").lower() == "true"

if not VERIFY_SSL:
    # Приглушуємо попередження про незахищене SSL-з'єднання у консолі
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Master switch: flip to True to make data_access/*.py call the real API
USE_BACKEND_API = os.environ.get("USE_BACKEND_API", "false").lower() == "true"