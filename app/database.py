from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Railway inyecta DATABASE_URL automáticamente cuando tienes PostgreSQL
# En local sigue usando SQLite como fallback
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Railway usa postgres://, SQLAlchemy necesita postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
else:
    # Fallback local: SQLite
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH  = os.path.normpath(os.path.join(BASE_DIR, "..", "data", "database.db"))
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
