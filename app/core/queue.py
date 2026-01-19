import os
from arq.connections import RedisSettings

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Parse Redis URL or use defaults
# ARQ RedisSettings is flexible
# For simplicity, if running in docker-compose, hostname is "redis"
redis_settings = RedisSettings(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
)

if "localhost" in REDIS_URL:
     redis_settings = RedisSettings(host="localhost", port=6379)
