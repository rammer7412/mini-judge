import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATA_DIR = os.getenv("DATA_DIR", "/data")
DEFAULT_SAMPLE_COUNT = int(os.getenv("DEFAULT_SAMPLE_COUNT", "3"))
