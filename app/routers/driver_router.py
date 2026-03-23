from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import shutil, uuid

from app.database import get_db
from app.models import Driver, Ride
from app.websocket_manager import manager
from app.auth import crear_token

router = APIRouter(prefix="/driver", tags=["Drivers"])


class DriverRegister(BaseModel):
    nombre: str
    telefono: str
    placa: Optional[str] = None
    sindicato_id: int


class DriverLogin(BaseModel):
    telefono: str


# ── RUTAS ESTÁTICAS PRIMERO (antes de /{driver_id}) ──────────────

@router.post("/register")
def register_driver(data: DriverRegister, db: Session = Depends(get_db)):
    if db.query(Driver).filter(Driver.telefono == data.telefono).first():
        raise HTTPException(status_code=400, detail="Teléfono ya registrado")
    driver = Driver(
        nombre=data.nombre, telefono=data.telefono, placa=data.placa,
        sindicato_id=data.sindicato_id, estado="DISPONIBLE", estado_registro="APROBADO"
    )
    db.add(driver); db.commit(); db.refresh(driver)
    return {"status": "registered", "driver_id": driver.id,
            "token": crear_token(driver.id, data.sindicato_id)}


@router.post("/registro")
async def registro_conductor(
    nombre: str = Form(...), telefono: str = Form(...),
    placa: str = Form(...), sindicato_id: int = Form(...),
    foto: UploadFile = File(None), db: Session = Depends(get_db)
):
    if db.query(Driver).filter(Driver.telefono == telefono).first():
        raise HTTPException(status_code=400, detail="Teléfono ya registrado")
    foto_url = None
    if foto and foto.filename:
        ext = foto.filename.split(".")[-1].lower()
        nombre_archivo = f"{uuid.uuid4().hex}.{ext}"
        ruta = f"/home/raspberrypi3/mototaxi_server/app/static/fotos/{nombre_archivo}"
        with open(ruta, "wb") as f:
            shutil.copyfileobj(foto.file, f)
        foto_url = f"/static/fotos/{nombre_archivo}"
    driver = Driver(
        nombre=nombre, telefono=telefono, placa=placa,
        sindicato_id=sindicato_id, estado="INACTIVO",
        estado_registro="PENDIENTE", foto_url=foto_url
    )
    db.add(driver); db.commit(); db.refresh(driver)
    return {"status": "pendiente", "driver_id": driver.id,
            "mensaje": "Registro enviado. El operador debe aprobarlo."}


@router.post("/login")
def login_driver(data: DriverLogin, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.telefono == data.telefono).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    if driver.estado_registro == "PENDIENTE":
        raise HTTPException(status_code=403, detail="Tu registro está pendiente de aprobación")
    if driver.estado_registro == "RECHAZADO":
        raise HTTPException(status_code=403, detail="Tu registro fue rechazado. Contacta a tu sindicato")
    return {"status": "ok", "driver_id": driver.id, "nombre": driver.nombre,
            "sindicato_id": driver.sindicato_id,
            "token": crear_token(driver.id, driver.sindicato_id)}


@router.post("/location")
def update_location(
    driver_id: int, lat: float, lon: float,
    background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    driver.lat = lat; driver.lon = lon; db.commit()
    background_tasks.add_task(manager.broadcast, {"driver_id": driver_id, "lat": lat, "lon": lon})
    return {"status": "updated", "driver_id": driver_id}


@router.get("/lista/pendientes")
def conductores_pendientes(sindicato_id: int = None, db: Session = Depends(get_db)):
    q = db.query(Driver).filter(Driver.estado_registro == "PENDIENTE")
    if sindicato_id:
        q = q.filter(Driver.sindicato_id == sindicato_id)
    return [{"driver_id": d.id, "nombre": d.nombre, "telefono": d.telefono,
             "placa": d.placa, "sindicato_id": d.sindicato_id,
             "foto_url": d.foto_url, "estado_registro": d.estado_registro}
            for d in q.all()]


@router.get("/lista/todos")
def todos_conductores(sindicato_id: int = None, db: Session = Depends(get_db)):
    q = db.query(Driver)
    if sindicato_id:
        q = q.filter(Driver.sindicato_id == sindicato_id)
    return [{"driver_id": d.id, "nombre": d.nombre, "telefono": d.telefono,
             "placa": d.placa, "sindicato_id": d.sindicato_id,
             "estado": d.estado, "estado_registro": d.estado_registro,
             "foto_url": d.foto_url}
            for d in q.all()]


@router.post("/aprobar/{driver_id}")
def aprobar_conductor(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    driver.estado_registro = "APROBADO"
    driver.estado = "DISPONIBLE"
    db.commit()
    return {"status": "aprobado", "driver_id": driver_id, "nombre": driver.nombre}


@router.post("/rechazar/{driver_id}")
def rechazar_conductor(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    driver.estado_registro = "RECHAZADO"
    driver.estado = "INACTIVO"
    db.commit()
    return {"status": "rechazado", "driver_id": driver_id}


@router.post("/disponible/{driver_id}")
def set_disponible(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    driver.estado = "DISPONIBLE"
    db.commit()
    return {"status": "DISPONIBLE", "driver_id": driver_id}


# ── RUTAS DINÁMICAS AL FINAL ──────────────────────────────────────

@router.get("/estado/{telefono}")
def estado_registro(telefono: str, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.telefono == telefono).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    mensajes = {
        "PENDIENTE": "Registro pendiente de aprobacion por el operador.",
        "APROBADO":  "Registro aprobado. Ya puedes recibir viajes.",
        "RECHAZADO": "Registro rechazado. Contacta al operador de tu sindicato."
    }
    return {
        "driver_id":       driver.id,
        "nombre":          driver.nombre,
        "estado_registro": driver.estado_registro,
        "estado":          driver.estado,
        "mensaje":         mensajes.get(driver.estado_registro, "Estado desconocido")
    }


@router.get("/{driver_id}")
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    return {"driver_id": driver.id, "nombre": driver.nombre, "placa": driver.placa,
            "sindicato_id": driver.sindicato_id, "estado": driver.estado,
            "estado_registro": driver.estado_registro,
            "foto_url": driver.foto_url, "lat": driver.lat, "lon": driver.lon}


@router.get("/{driver_id}/rides")
def get_driver_rides(driver_id: int, db: Session = Depends(get_db)):
    rides = db.query(Ride).filter(
        Ride.driver_id == driver_id, Ride.status == "ASIGNADO").all()
    return [{"ride_id": r.id, "origin_lat": r.origin_lat, "origin_lon": r.origin_lon,
             "destino": r.destino, "tarifa": r.tarifa,
             "passenger_phone": r.passenger_phone, "status": r.status}
            for r in rides]


@router.get("/{driver_id}/historial")
def historial_conductor(driver_id: int, limit: int = 20, db: Session = Depends(get_db)):
    from app.models import Ride
    rides = db.query(Ride).filter(
        Ride.driver_id == driver_id
    ).order_by(Ride.created_at.desc()).limit(limit).all()
    return [
        {
            "ride_id":    r.id,
            "destino":    r.destino,
            "tarifa":     r.tarifa,
            "status":     r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rides
    ]
