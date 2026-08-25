import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    "github_tracker",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
)