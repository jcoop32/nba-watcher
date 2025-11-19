import os
import redis
import json
from dotenv import load_dotenv

load_dotenv()

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_client = redis.from_url(redis_url, decode_responses=True)
except Exception as e:
    print(f"Warning: Could not connect to Redis. Caching will be disabled. Error: {e}")
    redis_client = None

def get_cache(key):
    """Retrieve data from Redis and deserialize JSON."""
    if not redis_client: return None
    try:
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        print(f"Redis Get Error: {e}")
        return None

def set_cache(key, data, timeout=300):
    """Serialize data to JSON and save to Redis with expiration."""
    if not redis_client: return
    try:
        redis_client.setex(key, timeout, json.dumps(data))
    except Exception as e:
        print(f"Redis Set Error: {e}")
