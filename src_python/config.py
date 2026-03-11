import os
from dotenv import load_dotenv

load_dotenv()

config = {
    "port": int(os.getenv("PORT", "3000")),
    "env": os.getenv("NODE_ENV", "development"),
    "database": {
        "path": os.getenv("DATABASE_PATH", "./data/patients.db"),
    },
    "vapi": {
        "api_key": os.getenv("VAPI_API_KEY", ""),
        "phone_number_id": os.getenv("VAPI_PHONE_NUMBER_ID", ""),
        "webhook_secret": os.getenv("VAPI_WEBHOOK_SECRET", ""),
    },
    "logging": {
        "level": os.getenv("LOG_LEVEL", "info"),
    },
}
