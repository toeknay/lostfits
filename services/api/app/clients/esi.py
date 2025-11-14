"""ESI (EVE Swagger Interface) API client."""

import asyncio
import json
from typing import Any

import httpx
from loguru import logger
from redis import Redis
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


class ESIClient:
    """Client for interacting with EVE Online's ESI API."""

    def __init__(self) -> None:
        self.base_url = str(settings.esi_base)
        self.user_agent = settings.esi_user_agent
        self.timeout = settings.esi_timeout_secs
        self.max_qps = settings.esi_max_qps
        self.session = httpx.Client(
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
        )
        # Simple rate limiting: minimum time between requests
        self._min_request_interval = 1.0 / self.max_qps if self.max_qps > 0 else 0
        self._last_request_time = 0.0
        # Redis cache for ESI responses
        self._redis = Redis.from_url(settings.redis_url, decode_responses=True)

    def __enter__(self) -> "ESIClient":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.session.close()

    async def _rate_limit(self) -> None:
        """Simple rate limiting by sleeping if needed."""
        if self._min_request_interval > 0:
            import time

            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - elapsed)
            self._last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def get_type(self, type_id: int) -> dict[str, Any] | None:
        """
        Fetch item type information from ESI with Redis caching.
        Item types never change, so we cache them indefinitely.

        Args:
            type_id: The EVE item type ID

        Returns:
            dict with keys like 'name', 'description', 'group_id', etc.
            None if type not found

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        cache_key = f"esi:type:{type_id}"

        # Try cache first
        try:
            cached = self._redis.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for type {type_id}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read error for type {type_id}: {e}")

        # Cache miss - fetch from ESI
        logger.debug(f"Cache MISS for type {type_id}, fetching from ESI")
        url = f"{self.base_url}/universe/types/{type_id}/"
        try:
            response = self.session.get(url)
            if response.status_code == 404:
                logger.warning(f"Type {type_id} not found in ESI")
                return None

            response.raise_for_status()
            data = response.json()
            logger.debug(f"Fetched type {type_id}: {data.get('name')}")

            # Cache the result indefinitely (item types don't change)
            try:
                self._redis.set(cache_key, json.dumps(data))
                logger.debug(f"Cached type {type_id}")
            except Exception as e:
                logger.warning(f"Failed to cache type {type_id}: {e}")

            return data

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch type {type_id} from ESI: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def get_killmail(self, killmail_id: int, killmail_hash: str) -> dict[str, Any] | None:
        """
        Fetch full killmail details from ESI.

        Args:
            killmail_id: The killmail ID
            killmail_hash: The killmail hash for authentication

        Returns:
            dict with full killmail data
            None if killmail not found

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        url = f"{self.base_url}/killmails/{killmail_id}/{killmail_hash}/"
        try:
            response = self.session.get(url)
            if response.status_code == 404:
                logger.warning(f"Killmail {killmail_id} not found in ESI")
                return None

            response.raise_for_status()
            data = response.json()
            logger.debug(f"Fetched killmail {killmail_id} from ESI")
            return data

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch killmail {killmail_id} from ESI: {e}")
            raise

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
