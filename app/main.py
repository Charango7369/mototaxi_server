from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from app.database import Base, engine, get_db
from app.models import Driver, Ride
from app.schemas import DriverLocation, RideRequest
from app.assigner import find_nearest_driver

#from app.routers import driver_router

# 🔥 Primero se crea la app
app = FastAPI()
from app.routers import driver_router
from app.routers import ride_router

# 🔥 Incluir routers 
app.include_router(driver_router.router)
app.include_router(ride_router.router)
# 🔥 Crear tablas
Base.metadata.create_all(bind=engine)

# 🔥 Configuración de archivos estáticos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))



# -----------------------------
# SOLICITAR VIAJE
# -----------------------------
#@app.post("/ride/request")
#def request_ride(ride: RideRequest, db: Session = Depends(get_db)):
#    driver = find_nearest_driver(db, ride.lat, ride.lon)
#
#    if driver is None:
#        return {"status": "no drivers available"}
#
#    new_ride = Ride(
#        driver_id=driver.id,
#        passenger_lat=ride.lat,
#        passenger_lon=ride.lon,
#        status="ASIGNADO"
#    )
#
#    db.add(new_ride)
#    db.commit()
#    db.refresh(new_ride)
#
#    return {
#        "ride_id": new_ride.id,
#        "driver_id": driver.id,
#        "status": "ASIGNADO"
#    }


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
@app.post("/ride/{ride_id}/status")
def update_ride_status(ride_id: int, status: str, db: Session = Depends(get_db)):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()

    if ride:
        ride.status = status
        db.commit()

    return {"status": status}


# -----------------------------
# ACCIONES DE VIAJE
# -----------------------------
@app.post("/ride/{ride_id}/accept")
def accept_ride(ride_id: int, db: Session = Depends(get_db)):
    return update_ride_status(ride_id, "ACEPTADO", db)


@app.post("/ride/{ride_id}/start")
def start_ride(ride_id: int, db: Session = Depends(get_db)):
    return update_ride_status(ride_id, "EN_VIAJE", db)


@app.post("/ride/{ride_id}/finish")
def finish_ride(ride_id: int, db: Session = Depends(get_db)):
    return update_ride_status(ride_id, "FINALIZADO", db)