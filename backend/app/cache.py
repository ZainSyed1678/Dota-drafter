import threading
from collections import OrderedDict
from typing import Any, Optional


class LRUCache:
    """Thread-safe LRU cache for FastAPI response caching."""
    def __init__(self, capacity: int = 1024):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: Any) -> Optional[Any]:
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            self.hits += 1
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: Any, value: Any) -> None:
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

    def clear(self) -> None:
        with self.lock:
            self.cache.clear()

    def stats(self) -> dict:
        with self.lock:
            return {
                "size": len(self.cache),
                "capacity": self.capacity,
                "hits": self.hits,
                "misses": self.misses,
                "hit_ratio": round(self.hits / (self.hits + self.misses), 3) if (self.hits + self.misses) > 0 else 0.0
            }


draft_cache = LRUCache(capacity=1024)
