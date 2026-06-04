from prometheus_client import Counter
from prometheus_client import Histogram


REQUEST_COUNT = Counter(
    "dota_requests_total",
    "Total API requests"
)

CACHE_HITS = Counter(
    "dota_cache_hits_total",
    "Total Redis cache hits"
)

CACHE_MISSES = Counter(
    "dota_cache_misses_total",
    "Total Redis cache misses"
)

SUGGEST_LATENCY = Histogram(
    "dota_suggest_latency_seconds",
    "Suggest endpoint latency"
)