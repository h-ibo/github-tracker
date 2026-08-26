import os
from celery import Celery

# Redis bağlantı adresini alıyoruz
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

# Celery uygulamamızı oluşturuyoruz
celery_app = Celery(
    "repotracker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.workers"]  # Celery'e task'ları (görevleri) nerede bulacağını söylüyoruz
)

# Celery Beat Zamanlaması
celery_app.conf.beat_schedule = {
    # Görevin adı
    "check-repos-every-5-min": {
        "task": "app.workers.check_all_repos",
        "schedule": 300.0,  # 300 saniye = 5 dakikada bir otomatik çalışacak
    },
}