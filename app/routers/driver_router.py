from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Driver
from app.schemas import DriverLocation

router = APIRouter(prefix="/driver", tags=["Drivers"])


# -----------------------------
# REGISTRAR CONDUCTOR
# -----------------------------
@router.post("/register")
def register_driver(nombre: str, telefono: str, db: Session = Depends(get_db)):
    driver = Driver(
        nombre=nombre,
        telefono=telefono,
        estado="DISPONIBLE"
    )

    db.add(driver)
    db.commit()
    db.refresh(driver)

    return {"driver_id": driver.id, "status": "registered"}


# -----------------------------
# LOGIN CONDUCTOR
# -----------------------------
@router.post("/login")
def driver_login(telefono: str, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.telefono == telefono).first()

    if not driver:
        return {"status": "not_found"}

    return {
        "status": "ok",
        "driver_id": driver.id,
        "nombre": driver.nombre
    }


# -----------------------------
# ACTUALIZAR UBICACIÓN
# -----------------------------
@router.post("/location")
def update_location(data: DriverLocation, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == data.driver_id).first()

    if driver:
        driver.lat = data.lat
        driver.lon = data.lon
        db.commit()

    return {"status": "location updated"}


# -----------------------------
# VER CONDUCTORES
# -----------------------------
@router.get("/all")
def get_drivers(db: Session = Depends(get_db)):
    drivers = db.query(Driver).all()

    return [
        {"id": d.id, "lat": d.lat, "lon": d.lon}
        for d in drivers
    ]
