import asyncio
import httpx
from datetime import datetime
from sqlmodel import Session, select

from app.celery_app import celery_app
from app.core.database import engine
from app.models.models import TrackedRepo, RepoEvent
from app.core.github import fetch_repo_commits_async

async def async_check_repos():
    with Session(engine) as session:
        repos = session.exec(select(TrackedRepo)).all()
        if not repos:
            print("Takip edilen repo yok, tarama atlandı.")
            return

        sem = asyncio.Semaphore(5)
        
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

        async with httpx.AsyncClient() as client:
            tasks = [fetch_latest_data(r, client) for r in repos]
            results = await asyncio.gather(*tasks)

        new_events_count = 0
        for data in results:
            if not data: continue
            
            repo = session.get(TrackedRepo, data["repo_id"])
            if repo.last_known_commit_sha != data["sha"]:
                new_event = RepoEvent(
                    tracked_repo_id=repo.id,
                    event_type="new_commit",
                    title=data["message"][:100],
                    url=data["url"]
                )
                session.add(new_event)
                repo.last_known_commit_sha = data["sha"]
                repo.last_checked_at = datetime.utcnow()
                session.add(repo)
                new_events_count += 1
                repo.last_checked_at = datetime.utcnow()
                session.add(repo)
                new_events_count += 1
                print(f"[!] YENİ GÜNCELLEME: {repo.repo_name} için yeni commit yakalandı!")

                try:
                    async with httpx.AsyncClient() as push_client:
                        await push_client.post(
                            "http://api:8000/ws/trigger-alert",
                            json={
                                "repo_name": f"{repo.owner}/{repo.repo_name}", 
                                "title": data["message"][:100]
                            }
                        )
                except Exception as e:
                    print(f"WebSocket tetikleme hatası: {e}")
               

        if new_events_count > 0:
                print(f"[!] YENİ GÜNCELLEME: {repo.repo_name} için yeni commit yakalandı!")

        if new_events_count > 0:
            session.commit()
            
        print(f"[*] Arka plan taraması bitti. {new_events_count} yeni olay bulundu.")

@celery_app.task
def check_all_repos():
    asyncio.run(async_check_repos())