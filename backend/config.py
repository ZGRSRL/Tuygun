import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache
import urllib.parse

class Settings(BaseSettings):
    PROJECT_NAME: str = "TUYGUN"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "zgrwise"
    DATABASE_URL: Optional[str] = None

    # Security
    SECURITY_USER: str = "admin"
    SECURITY_PASSWORD: str = "secret"

    # App specific
    # Default path inside Docker container
    OBSIDIAN_VAULT_PATH: str = "/app/obsidian_vault"
    OPENAI_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        # .env dosyasını parent directory'de ara (Docker dışında çalışırken)
        # Ancak Docker içinde .env genelde root'ta olmaz, env var olarak gelir.
        # Bu yüzden extra="ignore" ekleyebiliriz veya path'i dinamik yapabiliriz.
        env_file_encoding = 'utf-8'
        extra = "ignore" 

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        password_encoded = urllib.parse.quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql://{self.POSTGRES_USER}:{password_encoded}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
