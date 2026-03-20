from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import os
# Crear carpeta si no existe
os.makedirs("data", exist_ok=True)

# Ruta de la base de datos SQLite
# DATABASE_URL = "sqlite:///./data/database.db"
DATABASE_URL = "sqlite:///./test.db"
# Motor de conexión
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # necesario para SQLite
)

# Sesiones de base de datos
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para los modelos
Base = declarative_base()
# 🔥 ESTA ES LA CLAVE
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()