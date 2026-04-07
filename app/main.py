from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# Middleware para forzar upgrade WebSocket en Railway
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class WSUpgradeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/ws"):
            # Asegurar headers correctos para WebSocket
            headers = dict(request.headers)
            headers["upgrade"] = "websocket"
        return await call_next(request)

app.add_middleware(WSUpgradeMiddleware)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(driver_router.router)
app.include_router(ride_router.router)
app.include_router(ws_router.router)
app.include_router(stats_router.router)
app.include_router(monitor_router.router)

Base.metadata.create_all(bind=engine)

@app.get("/", response_class=FileResponse)
def root():
    return FileResponse(os.path.join(STATIC_DIR, "pasajero.html"))

@app.get("/pasajero", response_class=FileResponse)
def pasajero():
    return FileResponse(os.path.join(STATIC_DIR, "pasajero.html"))

@app.get("/conductor", response_class=FileResponse)
def conductor():
    return FileResponse(os.path.join(STATIC_DIR, "conductor.html"))

@app.get("/operador", response_class=FileResponse)
def operador():
    return FileResponse(os.path.join(STATIC_DIR, "map.html"))

@app.get("/registro", response_class=FileResponse)
def registro():
    return FileResponse(os.path.join(STATIC_DIR, "registro.html"))

@app.get("/estadisticas", response_class=FileResponse)
def estadisticas():
    return FileResponse(os.path.join(STATIC_DIR, "estadisticas.html"))

@app.get("/monitor", response_class=FileResponse)
def monitor():
    return FileResponse(os.path.join(STATIC_DIR, "monitor_dashboard.html"))

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
