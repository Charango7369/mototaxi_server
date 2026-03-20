from fastapi import BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.models import Driver
from app.websocket_manager import manager


# -----------------------------
# REGISTRAR CONDUCTOR
# -----------------------------
def register_driver(db: Session, nombre: str, telefono: str):
    driver = Driver(
        nombre=nombre,
        telefono=telefono,
        estado="DISPONIBLE"
    )

    db.add(driver)
    db.commit()
    db.refresh(driver)

    return {
        "driver_id": driver.id,
        "status": "registered"
    }


# -----------------------------
# LOGIN
# -----------------------------
def login_driver(db: Session, telefono: str):
    driver = db.query(Driver).filter(Driver.telefono == telefono).first()

    if not driver:
        return {"status": "not_found"}

    # Token simple (MVP)
    token = f"driver-{driver.id}"

    return {
        "status": "ok",
        "driver_id": driver.id,
        "nombre": driver.nombre,
        "token": token
    }
    


def update_driver_location(db, driver_id, lat, lon):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()

    if not driver:
        return {"error": "Driver not found"}

    driver.lat = lat
    driver.lon = lon

    db.commit()

    return {"status": "updated"}