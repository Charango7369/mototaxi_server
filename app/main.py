from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import os

from app.database import Base, engine, get_db
from app.models import Ride
from app.routers import driver_router, ride_router
from app.services.ride_service import update_ride_status

from app.dependencies import get_current_driver
from app.models import Driver
from app.routers import ws_router

from fastapi.staticfiles import StaticFiles
app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)
# Routers
app.include_router(driver_router.router)
app.include_router(ride_router.router)
app.include_router(ws_router.router)
# Crear tablas
Base.metadata.create_all(bind=engine)

# -----------------------------
# VIAJES DEL CONDUCTOR
# -----------------------------
@app.get("/driver/{driver_id}/rides")
def get_driver_rides(driver_id: int, db: Session = Depends(get_db)):
    rides = db.query(Ride).filter(
        Ride.driver_id == driver_id,
        Ride.status == "ASIGNADO"
    ).all()

    return [
        {
            "ride_id": r.id,
            "lat": r.passenger_lat,
            "lon": r.passenger_lon,
            "status": r.status
        }
        for r in rides
    ]


# -----------------------------
# ACTUALIZAR ESTADO VIAJE
# -----------------------------

@app.post("/ride/{ride_id}/accept")
def accept_ride(
    ride_id: int,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver)
):
    return update_ride_status(db, ride_id, "ACEPTADO")

@app.post("/ride/{ride_id}/start")
def start_ride(
    ride_id: int, 
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver)
    ):

    return update_ride_status(db, ride_id, "EN_VIAJE")

@app.post("/ride/{ride_id}/finish")
def finish_ride(
    ride_id: int,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_current_driver)
    ):
    return update_ride_status(db, ride_id, "FINALIZADO")

