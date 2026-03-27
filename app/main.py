from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from app.database import Base, engine, get_db
from app.routers import driver_router, ride_router, ws_router, stats_router, monitor_router

app = FastAPI(title="MototaxiServer - Apolo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

app.include_router(driver_router.router)
app.include_router(ride_router.router)
app.include_router(ws_router.router)
app.include_router(stats_router.router)
app.include_router(monitor_router.router)

Base.metadata.create_all(bind=engine)


@app.post("/admin/init-db")
def init_db(db: Session = Depends(get_db)):
    from app.models import Sindicato
    if db.query(Sindicato).count() > 0:
        return {"status": "ya inicializado", "sindicatos": db.query(Sindicato).count()}
    sindicatos = [
        ("Sindicato TUICHI",                "TUICHI"),
        ("Sindicato AMAZONAS",              "AMAZONAS"),
        ("Sindicato MADIDI",                "MADIDI"),
        ("Sindicato 15 DE AGOSTO",          "15 DE AGOSTO"),
        ("Sindicato NORTENO",               "NORTENO"),
        ("Sindicato INMACULADA CONCEPCION", "INMACULADA CONCEPCION"),
    ]
    for nombre, zona in sindicatos:
        db.add(Sindicato(nombre=nombre, zona=zona, activo=1))
    db.commit()
    return {"status": "ok", "sindicatos_creados": len(sindicatos)}
