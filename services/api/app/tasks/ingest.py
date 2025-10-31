import os

from redis import Redis
from rq import Queue

# OLD (bad default for containers):
# redis = Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))

# NEW (correct default for Docker networking):
redis = Redis.from_url(os.environ.get("REDIS_URL", "redis://redis:6379/0"))
q = Queue("default", connection=redis)


def enqueue_demo() -> None:
    q.enqueue(process_demo, "hello lostfits")


def process_demo(msg: str) -> str:
    print("Processing task:", msg)
    return msg.upper()
