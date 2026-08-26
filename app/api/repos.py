from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import asyncio
import httpx
import time
from datetime import datetime
from app.models.models import RepoEvent

from app.core.database import get_session
from app.models.models import TrackedRepo
# Sadece yeni asenkron fonksiyonumuzu import ediyoruz
from app.core.github import fetch_repo_commits_async

router = APIRouter(prefix="/repos", tags=["Repos"])

# 1. Yeni Repo Ekleme
@router.post("/track", response_model=TrackedRepo)
def track_repo(repo: TrackedRepo, session: Session = Depends(get_session)):
    statement = select(TrackedRepo).where(
        TrackedRepo.owner == repo.owner, 
        TrackedRepo.repo_name == repo.repo_name
    )
    existing_repo = session.exec(statement).first()
    
    if existing_repo:
        raise HTTPException(status_code=400, detail="Bu repo zaten takip ediliyor.")
    
    session.add(repo)
    session.commit()
    session.refresh(repo)
    return repo

# 2. Takip Edilen Tüm Repoları Listeleme
@router.get("/track", response_model=List[TrackedRepo])
def get_tracked_repos(session: Session = Depends(get_session)):
    repos = session.exec(select(TrackedRepo)).all()
    return repos

# 3. Repo Takibini Bırakma (Silme)
@router.delete("/track/{repo_id}")
def untrack_repo(repo_id: int, session: Session = Depends(get_session)):
    repo = session.get(TrackedRepo, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo bulunamadı.")
    
    session.delete(repo)
    session.commit()
    return {"message": f"'{repo.repo_name}' isimli repo takipten çıkarıldı."}

@router.get("/test-async")
async def test_async_github():
    test_repos = [
        ("tiangolo", "fastapi"),
        ("pallets", "flask"),
        ("django", "django"),
        ("encode", "starlette"),
        ("pydantic", "pydantic")
    ]
    
    # EŞZAMANLI İSTEK SINIRI: Aynı anda en fazla 2 isteğe izin ver
    sem = asyncio.Semaphore(2)
    
    # Semaphore'u kullanan sarmalayıcı (wrapper) fonksiyon
    async def fetch_with_semaphore(owner, repo, client):
        async with sem:
            return await fetch_repo_commits_async(owner, repo, client)
            
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_with_semaphore(owner, repo, client) 
            for owner, repo in test_repos
        ]
        results = await asyncio.gather(*tasks)
        
    end_time = time.time()
    
    return {
        "message": "Async istekler (Semaphore korumalı) tamamlandı!",
        "gecen_sure_saniye": round(end_time - start_time, 2),
        "cekilen_repo_sayisi": len(results)
    }
# 5. Yeni Commit'leri Kontrol Etme ve Veritabanına Kaydetme
@router.post("/check-updates")
async def check_updates_manually(session: Session = Depends(get_session)):
    # Sistemdeki tüm takip edilen repoları al
    repos = session.exec(select(TrackedRepo)).all()
    if not repos:
        return {"message": "Takip edilen hiçbir repo yok."}
        
    sem = asyncio.Semaphore(5)
    
    # Sadece GitHub'dan veriyi çekip döndüren yardımcı fonksiyon
    async def fetch_latest_data(repo, client):
        async with sem:
            try:
                commits = await fetch_repo_commits_async(repo.owner, repo.repo_name, client)
                if commits:
                    return {
                        "repo_id": repo.id,
                        "sha": commits[0]["sha"],
                        "message": commits[0]["commit"]["message"],
                        "url": commits[0]["html_url"]
                    }
            except Exception as e:
                print(f"Hata ({repo.repo_name}): {e}")
            return None

    # 1. Aşama: Tüm GitHub isteklerini paralel atıp verileri topla
    async with httpx.AsyncClient() as client:
        tasks = [fetch_latest_data(r, client) for r in repos]
        results = await asyncio.gather(*tasks)
        
    # 2. Aşama: Veritabanı karşılaştırma ve kaydetme işlemleri
    new_events_count = 0
    for data in results:
        if not data:
            continue
            
        # İlgili repoyu veritabanından al
        repo = session.get(TrackedRepo, data["repo_id"])
        
        # Değişiklik var mı? (İlk eklemede last_known_commit_sha None'dur, bu da farklı sayılır)
        if repo.last_known_commit_sha != data["sha"]:
            
            # Yeni olayı (Event) oluştur
            new_event = RepoEvent(
                tracked_repo_id=repo.id,
                event_type="new_commit",
                title=data["message"][:100],  # Başlık çok uzun olmasın diye kesiyoruz
                url=data["url"]
            )
            session.add(new_event)
            
            # Reponun güncel SHA bilgisini güncelle
            repo.last_known_commit_sha = data["sha"]
            repo.last_checked_at = datetime.utcnow()
            session.add(repo)
            
            new_events_count += 1
            
    # Eğer yeni olay(lar) bulunduysa değişiklikleri veritabanına işle (commit)
    if new_events_count > 0:
        session.commit()
        
    return {
        "message": "Kontrol tamamlandı.",
        "taranan_repo_sayisi": len(repos),
        "bulunan_yeni_olay_sayisi": new_events_count
    }