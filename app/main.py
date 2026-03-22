# app/main.py
from fastapi import FastAPI
from sqlalchemy.orm import Session
import os

from app.database import Base, engine
from app.routers import driver_router, ride_router, ws_router
from app.routers import stats_router
from app.routers import monitor_router
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="MototaxiServer — Apolo")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

app.include_router(driver_router.router)
app.include_router(ride_router.router)
app.include_router(ws_router.router)
app.include_router(stats_router.router)
app.include_router(monitor_router.router)

Base.metadata.create_all(bind=engine)