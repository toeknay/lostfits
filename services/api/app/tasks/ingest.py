from rq import Queue
from redis import Redis
import os

redis = Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
q = Queue("default", connection=redis)

def enqueue_demo():
    q.enqueue(process_demo, "hello lostfits")

def process_demo(msg: str):
    print("Processing task:", msg)
    return msg.upper()
