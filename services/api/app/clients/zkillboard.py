"""zKillboard RedisQ API client for fetching killmails."""

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

# Updated URL as of May 2025
ZKILL_REDISQ_URL = "https://zkillredisq.stream/listen.php"


class ZKillboardClient:
    """Client for fetching killmails from zKillboard RedisQ API."""

    def __init__(self, timeout_seconds: int = 30):
        self.timeout = timeout_seconds
        # follow_redirects handles the /listen.php -> /object.php redirect (Aug 2025 change)
        self.session = httpx.Client(timeout=timeout_seconds, follow_redirects=True)

    def __enter__(self) -> "ZKillboardClient":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def fetch_killmail(self, queue_id: str = "lostfits") -> dict | None:
        """
        Fetch a single killmail from the RedisQ endpoint.

        Args:
            queue_id: Unique identifier for this app's queue (default: "lostfits")

        Returns:
            dict: Killmail package containing 'killID', 'killmail', and 'zkb' data
            None: If queue is empty (returns {"package": null})

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        try:
            # Use queueID to identify our app and maintain queue state
            params = {"queueID": queue_id}
            response = self.session.get(ZKILL_REDISQ_URL, params=params)
            response.raise_for_status()
            data = response.json()

            # RedisQ returns {"package": null} when queue is empty
            package = data.get("package")
            if package is None:
                logger.debug("RedisQ queue empty")
                return None

            killmail_id = package.get("killID")
            logger.info(f"Fetched killmail {killmail_id} from zKillboard RedisQ")
            return package

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch from zKillboard RedisQ: {e}")
            raise

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
