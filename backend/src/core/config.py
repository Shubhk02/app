from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hospital Management System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "hospital_management")
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        arbitrary_types_allowed=True,
        extra="allow"   # ✅ allows extra vars in .env
    )


# Create global settings object
settings = Settings()