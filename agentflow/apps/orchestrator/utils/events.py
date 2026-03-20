import json
from db.redis_client import get_redis


async def publish_event(run_id: str, event: dict):
    redis = await get_redis()
    await redis.publish(f"events:{run_id}", json.dumps(event))
