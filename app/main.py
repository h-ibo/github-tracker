from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import create_db_and_tables
from app.models.models import TrackedRepo, RepoEvent
from app.api import repos  # API router'ımızı dahil ediyoruz

# Uygulama ayağa kalkarken çalışacak olaylar
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Veritabanı tabloları oluşturuluyor...")
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# /repos endpoint'lerini ana uygulamaya bağlıyoruz
app.include_router(repos.router)

@app.get("/")
def read_root():
    return {"message": "Sistem aktif ve tablolar bağlandı!"}