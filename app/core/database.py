import os
from sqlmodel import SQLModel, create_engine
from sqlmodel import Session

# .env dosyasındaki veritabanı URL'sini alıyoruz
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:devpassword@db:5432/repotracker"
)

engine = create_engine(DATABASE_URL)

# Bu fonksiyon çağrıldığında, tanımlı tüm modelleri veritabanında tabloya çevirir
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
def get_session():
    with Session(engine) as session:
        yield session