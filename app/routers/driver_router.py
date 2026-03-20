from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import driver_service
from app.websocket_manager import manager  # 👈 ajusta si cambia el path

router = APIRouter(prefix="/driver", tags=["Drivers"])


@router.post("/location")
def update_location(
    driver_id: int,
    lat: float,
    lon: float,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    result = driver_service.update_driver_location(db, driver_id, lat, lon)

    background_tasks.add_task(
        manager.broadcast,
        {
            "driver_id": driver_id,
            "lat": lat,
            "lon": lon
        }
    )

    return result