from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    TOGETHER_API_KEY: str = ""

    PRIMARY_MODEL: str = "llama-3.3-70b-versatile"
    FAST_MODEL: str = "llama-3.1-8b-instant"

    DATABASE_PATH: str = "./research_agents.db"
    OUTPUT_DIR: str = "../research_outputs"
    LOG_DIR: str = "../logs"

    MAX_SEARCH_RESULTS: int = 8
    MAX_READ_URLS: int = 5
    REQUEST_TIMEOUT: int = 30

    model_config = {"env_file": ".env"}


settings = Settings()

Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.LOG_DIR).mkdir(parents=True, exist_ok=True)
