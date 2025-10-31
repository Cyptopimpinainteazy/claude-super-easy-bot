"""
Redis cache manager for real-time caching and rate limiting.
"""

import redis.asyncio as aioredis
from typing import Optional, Any, List, Dict
import json
import logging
import os
from datetime import timedelta
from math import floor
import time

logger = logging.getLogger(__name__)


class RedisCache:
    """Manages Redis caching, pub/sub, and rate limiting"""

    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 30):
        """
        Initialize Redis cache manager.

        Args:
            redis_url: Redis connection URL. If None, loads from REDIS_URL environment variable.
            default_ttl: Default TTL for cached items in seconds.
        """
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.key_prefix = "arbitrage:"
        self.redis_client: Optional[aioredis.Redis] = None

    async def initialize(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("✓ Redis cache initialized successfully")

        except Exception as e:
            logger.error(f"✗ Failed to initialize Redis: {e}")
            raise

    def _make_key(self, key: str) -> str:
        """Create prefixed key"""
        return f"{self.key_prefix}{key}"

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.redis_client:
            logger.warning("Redis not initialized")
            return False

        try:
            full_key = self._make_key(key)
            ttl_seconds = ttl or self.default_ttl

            # Serialize to JSON if not string
            if isinstance(value, str):
                serialized = value
            else:
                serialized = json.dumps(value, default=str)

            await self.redis_client.setex(full_key, ttl_seconds, serialized)
            return True
        except Exception as e:
            logger.warning(f"Failed to set cache key {key}: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None

        try:
            full_key = self._make_key(key)
            value = await self.redis_client.get(full_key)

            if value is None:
                return None

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.warning(f"Failed to get cache key {key}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False

        try:
            full_key = self._make_key(key)
            await self.redis_client.delete(full_key)
            return True
        except Exception as e:
            logger.warning(f"Failed to delete cache key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False

        try:
            full_key = self._make_key(key)
            return await self.redis_client.exists(full_key) > 0
        except Exception as e:
            logger.warning(f"Failed to check cache key {key}: {e}")
            return False

    async def increment(
        self, key: str, amount: int = 1, ttl: Optional[int] = None
    ) -> int:
        """Increment counter"""
        if not self.redis_client:
            return 0

        try:
            full_key = self._make_key(key)
            new_value = await self.redis_client.incr(full_key, amount)

            if ttl:
                await self.redis_client.expire(full_key, ttl)

            return new_value
        except Exception as e:
            logger.warning(f"Failed to increment cache key {key}: {e}")
            return 0

    async def get_many(self, keys: List[str]) -> List[Optional[Any]]:
        """Get multiple keys in one call"""
        if not self.redis_client:
            return [None] * len(keys)

        try:
            full_keys = [self._make_key(k) for k in keys]
            values = await self.redis_client.mget(full_keys)

            result = []
            for value in values:
                if value is None:
                    result.append(None)
                else:
                    try:
                        result.append(json.loads(value))
                    except json.JSONDecodeError:
                        result.append(value)

            return result
        except Exception as e:
            logger.warning(f"Failed to get multiple cache keys: {e}")
            return [None] * len(keys)

    async def set_many(self, items: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple key-value pairs"""
        if not self.redis_client:
            return False

        try:
            ttl_seconds = ttl or self.default_ttl
            pipe = self.redis_client.pipeline()

            for key, value in items.items():
                full_key = self._make_key(key)
                serialized = (
                    value if isinstance(value, str) else json.dumps(value, default=str)
                )
                pipe.setex(full_key, ttl_seconds, serialized)

            await pipe.execute()
            return True
        except Exception as e:
            logger.warning(f"Failed to set multiple cache keys: {e}")
            return False

    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to Redis pub/sub channel"""
        if not self.redis_client:
            return 0

        try:
            full_channel = self._make_key(channel)
            serialized = (
                message
                if isinstance(message, str)
                else json.dumps(message, default=str)
            )
            subscribers = await self.redis_client.publish(full_channel, serialized)
            return subscribers
        except Exception as e:
            logger.warning(f"Failed to publish to channel {channel}: {e}")
            return 0

    async def rate_limit(
        self, key: str, max_requests: int, window_seconds: int
    ) -> bool:
        """
        Implement sliding window rate limiting.

        Args:
            key: Rate limit key
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if request allowed, False if rate limited
        """
        if not self.redis_client:
            return True  # Allow if Redis unavailable

        try:
            full_key = self._make_key(f"ratelimit:{key}")
            current_time = time.time()
            window_start = current_time - window_seconds

            # Remove old entries
            await self.redis_client.zremrangebyscore(full_key, 0, window_start)

            # Count current requests in window
            count = await self.redis_client.zcard(full_key)

            if count < max_requests:
                # Add current request
                await self.redis_client.zadd(
                    full_key, {str(current_time): current_time}
                )
                # Set expiry
                await self.redis_client.expire(full_key, window_seconds + 1)
                return True
            else:
                return False
        except Exception as e:
            logger.warning(f"Rate limit check failed for {key}: {e}")
            return True  # Allow if check fails

    async def cache_opportunities(
        self, opportunities: List[dict], ttl: int = 10
    ) -> bool:
        """Cache opportunities"""
        return await self.set("opportunities:latest", opportunities, ttl=ttl)

    async def get_cached_opportunities(self, chain: Optional[str] = None) -> List[dict]:
        """Get cached opportunities"""
        if chain:
            result = await self.get(f"opportunities:{chain}")
        else:
            result = await self.get("opportunities:latest")
        return result or []

    async def cache_stats(self, stats: dict, ttl: int = 5) -> bool:
        """Cache bot statistics"""
        return await self.set("stats:current", stats, ttl=ttl)

    async def get_cached_stats(self) -> Optional[dict]:
        """Get cached statistics"""
        return await self.get("stats:current")

    async def cache_gas_prices(self, gas_prices: dict, ttl: int = 10) -> bool:
        """Cache gas prices"""
        return await self.set("gas_prices:latest", gas_prices, ttl=ttl)

    async def get_cached_gas_prices(self) -> Optional[dict]:
        """Get cached gas prices"""
        return await self.get("gas_prices:latest")

    async def close(self) -> None:
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("✓ Redis connection closed")


# Global Redis cache instance
_redis_cache: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """Get or create global Redis cache instance"""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache
