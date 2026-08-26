from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime

# 1. Ana Tablomuz: Takip edilen GitHub depoları
class TrackedRepo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner: str  # Örn: "tiangolo"
    repo_name: str  # Örn: "fastapi"
    added_by_user: str
    
    # Kontrol mekanizması için gereken alanlar
    last_checked_at: Optional[datetime] = None
    last_known_commit_sha: Optional[str] = None
    last_known_release_tag: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # İLİŞKİ: Bir reponun birden çok eventi (olayı) olabilir
    events: List["RepoEvent"] = Relationship(back_populates="repo")

# 2. Alt Tablomuz: Depolarda gerçekleşen olaylar
class RepoEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Bu olayın hangi repoya ait olduğunu belirten bağlantı (Foreign Key)
    tracked_repo_id: int = Field(foreign_key="trackedrepo.id")
    
    event_type: str  # "new_commit", "new_release", "new_issue"
    title: str
    url: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    # İLİŞKİ: Bu eventin ait olduğu ana repoyu çağırabilmek için
    repo: Optional[TrackedRepo] = Relationship(back_populates="events")