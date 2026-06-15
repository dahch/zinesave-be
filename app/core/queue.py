from urllib.parse import urlparse

import certifi
from arq.connections import RedisSettings

from app.core.config import settings

REDIS_URL = settings.REDIS_URL

# Parse Redis URL or use defaults
# ARQ RedisSettings is flexible
if REDIS_URL:
    parsed = urlparse(REDIS_URL)
    ssl_ca_certs = None
    if parsed.scheme == "rediss":
        ssl_ca_certs = certifi.where()
        
    redis_settings = RedisSettings(
        host=parsed.hostname,
        port=parsed.port or 6379,
        password=parsed.password,
        ssl=(parsed.scheme == "rediss"),
        ssl_ca_certs=ssl_ca_certs,
    )
else:
    # For simplicity, if running in docker-compose, hostname is "redis"
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=int(settings.REDIS_PORT),
    )

