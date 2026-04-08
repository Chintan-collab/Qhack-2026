import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "AI Sales Coach API")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")


settings = Settings()
