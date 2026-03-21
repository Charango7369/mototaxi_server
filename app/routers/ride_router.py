from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import RideRequest
from app.assigner import find_nearest_driver
from app.models import Ride, Driver
from app.services.ride_service import update_ride_status
from app.websocket_manager import manager

router = APIRouter(prefix="/ride", tags=["Rides"])


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

    return {"status": "assigned", "ride_id": ride.id, "driver_id": driver_id}


@router.post("/{ride_id}/accept")
def accept_ride(ride_id: int, db: Session = Depends(get_db)):
    return update_ride_status(db, ride_id, "ACEPTADO")


@router.post("/{ride_id}/start")
def start_ride(ride_id: int, db: Session = Depends(get_db)):
    return update_ride_status(db, ride_id, "EN_VIAJE")


@router.post("/{ride_id}/finish")
def finish_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if ride and ride.driver_id:
        driver = db.query(Driver).filter(Driver.id == ride.driver_id).first()
        if driver:
            driver.estado = "DISPONIBLE"
            db.commit()
    return update_ride_status(db, ride_id, "FINALIZADO")
