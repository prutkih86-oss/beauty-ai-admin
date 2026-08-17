import os
from dotenv import load_dotenv

load_dotenv()

# Backend API base URL (no trailing slash)
API_BASE_URL = os.environ.get(
    "API_BASE_URL", "http://beautyaiservice.polandcentral.cloudapp.azure.com:8000"
)

# Admin/staff account credentials for JWT auth (POST /api/users/token/)
# Set these in a .env file (or as environment variables):
#   API_EMAIL=...
#   API_PASSWORD=...
API_EMAIL = os.environ.get("API_EMAIL")
API_PASSWORD = os.environ.get("API_PASSWORD")

# Master switch: once credentials are set and confirmed working,
# flip this to True to make data_access/*.py call the real API
# instead of the local SQLite database.
USE_BACKEND_API = os.environ.get("USE_BACKEND_API", "false").lower() == "true"