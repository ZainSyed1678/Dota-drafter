import json

import redis


class CacheService:

    def __init__(self):

        self.redis = redis.Redis(
            host="redis",
            port=6379,
            decode_responses=True
        )

    def get(self, key):

        value = self.redis.get(key)

        if value:
            return json.loads(value)

        return None

    def set(
        self,
        key,
        value,
        ttl=3600
    ):

        self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )


cache_service = CacheService()