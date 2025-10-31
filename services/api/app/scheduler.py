import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.tasks.ingest import enqueue_demo

async def main():
    sched = AsyncIOScheduler(timezone="UTC")
    sched.add_job(enqueue_demo, "interval", minutes=1, id="demo")
    sched.start()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
