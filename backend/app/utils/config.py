from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # OpenAI Configuration
    OPENAI_API_KEY: str = "placeholder_key"
    
    # Database Configuration (SQLite Only)
    DB_TYPE: str = "sqlite"
    SQLITE_DB_PATH: str = "../database/sample_data/chinook.db"
    
    # Application Configuration
    API_PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings() 