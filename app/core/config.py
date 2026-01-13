import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    APP_TITLE: str = "Mini Judge (MVP)"
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DATA_DIR: str = os.getenv("DATA_DIR", "/data")
    DEFAULT_SAMPLE_COUNT: int = int(os.getenv("DEFAULT_SAMPLE_COUNT", "3"))
    MAX_SAMPLE_COUNT_HARD_LIMIT: int = int(os.getenv("MAX_SAMPLE_COUNT_HARD_LIMIT", "20"))

settings = Settings()
