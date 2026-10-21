import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # FreeAccount OAuth
    FREEAGENT_CLIENT_ID: str = ""
    FREEAGENT_CLIENT_SECRET: str = ""
    FREEAGENT_REDIRECT_URI: str = os.environ.get("FREEAGENT_REDIRECT_URI", "https://your-app.railway.app/api/freeagent/callback")
    # In production this MUST be https (Railway provides the public URL)
    FREEAGENT_SANDBOX: bool = False
    # General
    SECRET_KEY: str = "change-me"
    DATABASE_URL: str = "sqlite:///./freeagent_reader.db"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
