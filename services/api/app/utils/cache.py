"""Redis cache utilities for static data."""

import json
from collections.abc import Callable
from functools import wraps
from typing import Any

from loguru import logger
from redis import Redis

from app.config import settings

# Redis client for caching
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


def cache_forever(key_prefix: str, exclude_first_arg: bool = False) -> Callable:
    """
    Decorator to cache function results in Redis indefinitely.
    Use for data that never changes (universe data, ESI static data).

    Args:
        key_prefix: Prefix for the cache key
        exclude_first_arg: If True, exclude the first positional argument from cache key
                          (useful for DB sessions that shouldn't affect caching)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Build cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}"

            # Add args to key if present (skip first arg if requested)
            cache_args = args[1:] if exclude_first_arg and args else args
            if cache_args:
                # Only include hashable, serializable args
                serializable_args = []
                for arg in cache_args:
                    if isinstance(arg, str | int | float | bool | type(None)):
                        serializable_args.append(str(arg))
                if serializable_args:
                    args_str = ":".join(serializable_args)
                    cache_key += f":{args_str}"

            # Add kwargs to key if present
            if kwargs:
                kwargs_str = ":".join(
                    f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None
                )
                if kwargs_str:
                    cache_key += f":{kwargs_str}"

            try:
                # Try to get from cache
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return json.loads(cached)

                # Cache miss - call function
                logger.debug(f"Cache MISS: {cache_key}")
                result = func(*args, **kwargs)

                # Store in cache (no expiration for static data)
                redis_client.set(cache_key, json.dumps(result))
                logger.debug(f"Cached result at: {cache_key}")

                return result

            except Exception as e:
                # If Redis fails, just call the function
                logger.warning(f"Cache error for {cache_key}: {e}")
                return func(*args, **kwargs)

        return wrapper

    return decorator


def invalidate_cache(pattern: str) -> int:
    """
    Invalidate cache keys matching a pattern.

    Args:
        pattern: Redis key pattern (e.g., "universe:*")

    Returns:
        Number of keys deleted
    """
    try:
        keys = redis_client.keys(pattern)
        if keys:
            deleted = redis_client.delete(*keys)
            logger.info(f"Invalidated {deleted} cache keys matching: {pattern}")
            return deleted
        return 0
    except Exception as e:
        logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")
        return 0
