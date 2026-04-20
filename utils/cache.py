"""
Semantic Cache for Gateway Analysis Results
"""
import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from redisvl.extensions.cache.llm import SemanticCache
from redisvl.utils.vectorize import HFTextVectorizer

_ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT_DIR / ".env")


class AnalysisCache:
    TTL_SECONDS = 600
    DISTANCE_THRESHOLD = 0.15

    def __init__(
        self,
        redis_url: Optional[str] = None,
        distance_threshold: float = DISTANCE_THRESHOLD
    ):
        redis_url = redis_url or "redis://localhost:6379"

        self.cache = SemanticCache(
            name="gateway_analysis",
            redis_url=redis_url,
            distance_threshold=distance_threshold,
            ttl=self.TTL_SECONDS,
            vectorizer=HFTextVectorizer("all-MiniLM-L6-v2")
        )
        self._stats = {"hits": 0, "misses": 0}

    async def get(self, prompt: str) -> Optional[dict]:
        if result := self.cache.check(prompt=prompt):
            self._stats["hits"] += 1
            try:
                return json.loads(result[0].get("response"))
            except (json.JSONDecodeError, TypeError):
                return None
        self._stats["misses"] += 1
        return None

    async def store(self, prompt: str, response: dict):
        self.cache.store(prompt=prompt, response=json.dumps(response))

    def get_stats(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0.0
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": round(hit_rate, 4),
            "total_requests": total,
        }

    def clear_stats(self):
        self._stats = {"hits": 0, "misses": 0}
