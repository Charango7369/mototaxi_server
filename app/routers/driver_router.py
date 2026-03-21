from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import Driver, Ride
from app.websocket_manager import manager

router = APIRouter(prefix="/driver", tags=["Drivers"])


class DriverRegister(BaseModel):
    nombre: str
    telefono: str
    placa: Optional[str] = None
    sindicato_id: int


class DriverLogin(BaseModel):
    telefono: str


@router.post("/register")
def register_driver(data: DriverRegister, db: Session = Depends(get_db)):
    if db.query(Driver).filter(Driver.telefono == data.telefono).first():
        raise HTTPException(status_code=400, detail="Teléfono ya registrado")
    driver = Driver(
        nombre=data.nombre,
        telefono=data.telefono,
        placa=data.placa,
        sindicato_id=data.sindicato_id,
        estado="DISPONIBLE"
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return {"status": "registered", "driver_id": driver.id, "token": f"driver-{driver.id}"}


@router.post("/login")
def login_driver(data: DriverLogin, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.telefono == data.telefono).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    return {"status": "ok", "driver_id": driver.id, "nombre": driver.nombre, "token": f"driver-{driver.id}"}


@router.post("/location")
def update_location(
    driver_id: int,
    lat: float,
    lon: float,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    driver.lat = lat
    driver.lon = lon
    db.commit()
    background_tasks.add_task(manager.broadcast, {"driver_id": driver_id, "lat": lat, "lon": lon})
    return {"status": "updated", "driver_id": driver_id}


@router.get("/{driver_id}")
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    return {
        "driver_id": driver.id,
        "nombre": driver.nombre,
        "placa": driver.placa,
        "sindicato_id": driver.sindicato_id,
        "estado": driver.estado,
        "lat": driver.lat,
        "lon": driver.lon
    }


@router.get("/{driver_id}/rides")
def get_driver_rides(driver_id: int, db: Session = Depends(get_db)):
    rides = db.query(Ride).filter(
        Ride.driver_id == driver_id,
        Ride.status == "ASIGNADO"
    ).all()
    return [
        {
            "ride_id": r.id,
            "origin_lat": r.origin_lat,
            "origin_lon": r.origin_lon,
            "destino": r.destino,
            "tarifa": r.tarifa,
            "passenger_phone": r.passenger_phone,
            "status": r.status
        }
        for r in rides
    ]


@router.post("/{driver_id}/disponible")
def set_disponible(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    driver.estado = "DISPONIBLE"
    db.commit()
    return {"status": "DISPONIBLE", "driver_id": driver_id}


@router.post("/{driver_id}/disponible")
def set_disponible(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    driver.estado = "DISPONIBLE"
    db.commit()
    return {"status": "DISPONIBLE", "driver_id": driver_id}
