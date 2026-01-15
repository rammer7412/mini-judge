import os

import redis

# -----------------------------------------------------------------------------
# Config & shared dependencies
# -----------------------------------------------------------------------------

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATA_DIR = os.getenv("DATA_DIR", "/data")
DEFAULT_SAMPLE_COUNT = int(os.getenv("DEFAULT_SAMPLE_COUNT", "3"))

# NOTE: decode_responses=True so redis returns strings (not bytes)
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# -----------------------------------------------------------------------------
# Submission status
# -----------------------------------------------------------------------------

# UI/클라이언트가 최종 결과로 간주하는 상태들
FINAL_STATUSES = {
    "ACCEPTED",
    "WRONG_ANSWER",
    "TIME_LIMIT_EXCEEDED",
    "MEMORY_LIMIT_EXCEEDED",
    "RUNTIME_ERROR",
    "COMPILATION_ERROR",
    "INTERNAL_ERROR",
    # worker.py legacy terminal status
    "DONE",
}
