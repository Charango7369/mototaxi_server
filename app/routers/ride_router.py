from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import RideRequest
from app.assigner import find_nearest_driver
from app.models import Ride, Driver
from app.services.ride_service import update_ride_status
from app.websocket_manager import manager
from app.dependencies import get_current_driver

router = APIRouter(prefix="/ride", tags=["Rides"])


# ─────────────────────────────
# SOLICITAR VIAJE (pasajero)
# ─────────────────────────────
@router.post("/request")
async def request_ride(
    data: RideRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    driver_id = find_nearest_driver(db, data, sindicato_id=data.sindicato_id)

    if not driver_id:
        return {"status": "no_driver_available"}

    ride = Ride(
        driver_id=driver_id,
        sindicato_id=data.sindicato_id,
        passenger_phone=data.passenger_phone,
        origin_lat=data.origin_lat,
        origin_lon=data.origin_lon,
        dest_lat=data.dest_lat,
        dest_lon=data.dest_lon,
        destino=data.destino,
        tarifa=data.tarifa,
        status="ASIGNADO"
    )

    db.add(ride)
    db.commit()
    db.refresh(ride)

    # 🔥 Notificar al conductor
    background_tasks.add_task(
        manager.send_to_driver,
        driver_id,
        {
            "event": "ride_assigned",
            "ride_id": ride.id,
            "passenger_phone": data.passenger_phone,
            "origin_lat": data.origin_lat,
            "origin_lon": data.origin_lon,
            "destino": data.destino,
            "tarifa": data.tarifa
        }
    )

    # 🔥 NUEVO: Notificar a operadores
    background_tasks.add_task(
        manager.broadcast_to_operators,
        {
            "event": "new_ride",
            "ride_id": ride.id,
            "driver_id": driver_id,
            "status": ride.status,
            "destino": data.destino,
            "tarifa": data.tarifa
        }
    )

    return {
        "status": "assigned",
        "ride_id": ride.id,
        "driver_id": driver_id
    }


# ─────────────────────────────
# VIAJES ACTIVOS (panel operador)
# ─────────────────────────────
@router.get("/activos")
def rides_activos(
    sindicato_id: int = None,
    db: Session = Depends(get_db)
):
    q = db.query(Ride).filter(
        Ride.status.in_(["ASIGNADO", "ACEPTADO", "EN_VIAJE"])
    )

    if sindicato_id:
        q = q.filter(Ride.sindicato_id == sindicato_id)

    rides = q.order_by(Ride.created_at.desc()).all()

    return [
        {
            "ride_id": r.id,
            "driver_id": r.driver_id,
            "sindicato_id": r.sindicato_id,
            "passenger_phone": r.passenger_phone,
            "destino": r.destino,
            "tarifa": r.tarifa,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rides
    ]


# ─────────────────────────────
# CANCELAR VIAJE
# ─────────────────────────────
@router.post("/{ride_id}/cancel")
def cancel_ride(
    ride_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()

    if not ride:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    if ride.status in ("FINALIZADO", "CANCELADO"):
        raise HTTPException(status_code=400, detail=f"No se puede cancelar un viaje {ride.status}")

    # liberar conductor
    if ride.driver_id:
        driver = db.query(Driver).filter(Driver.id == ride.driver_id).first()
        if driver:
            driver.estado = "DISPONIBLE"

    ride.status = "CANCELADO"
    db.commit()

    # 🔥 notificar operadores
    background_tasks.add_task(
        manager.broadcast_to_operators,
        {"event": "ride_cancelled", "ride_id": ride_id}
    )

    return {"status": "CANCELADO", "ride_id": ride_id}


# ─────────────────────────────
# ACEPTAR VIAJE
# ─────────────────────────────
@router.post("/{ride_id}/accept")
def accept_ride(
    ride_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    conductor: Driver = Depends(get_current_driver)
):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()

    if not ride:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    if ride.driver_id != conductor.id:
        raise HTTPException(status_code=403, detail="No es tu viaje")

    result = update_ride_status(db, ride_id, "ACEPTADO")

    # 🔥 Notificar operadores
    background_tasks.add_task(
        manager.broadcast_to_operators,
        {"event": "ride_accepted", "ride_id": ride_id, "driver_id": conductor.id}
    )

    return result


# ─────────────────────────────
# INICIAR VIAJE
# ─────────────────────────────
@router.post("/{ride_id}/start")
def start_ride(
    ride_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    conductor: Driver = Depends(get_current_driver)
):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()

    if not ride:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    if ride.driver_id != conductor.id:
        raise HTTPException(status_code=403, detail="No es tu viaje")

    result = update_ride_status(db, ride_id, "EN_VIAJE")

    # 🔥 Notificar operadores
    background_tasks.add_task(
        manager.broadcast_to_operators,
        {"event": "ride_started", "ride_id": ride_id}
    )

    return result


# ─────────────────────────────
# FINALIZAR VIAJE
# ─────────────────────────────
@router.post("/{ride_id}/finish")
def finish_ride(
    ride_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    conductor: Driver = Depends(get_current_driver)
):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()

    if not ride:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    if ride.driver_id != conductor.id:
        raise HTTPException(status_code=403, detail="No es tu viaje")

    driver = db.query(Driver).filter(Driver.id == conductor.id).first()
    if driver:
        driver.estado = "DISPONIBLE"
        db.commit()

    result = update_ride_status(db, ride_id, "FINALIZADO")

    # 🔥 Notificar operadores
    background_tasks.add_task(
        manager.broadcast_to_operators,
        {"event": "ride_finished", "ride_id": ride_id}
    )

    return result