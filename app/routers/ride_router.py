from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import RideRequest
from app.assigner import find_nearest_driver

router = APIRouter(prefix="/ride", tags=["Rides"])


# -----------------------------
# SOLICITAR VIAJE
# -----------------------------
@router.post("/request")
def request_ride(data: RideRequest, db: Session = Depends(get_db)):

    driver_id = find_nearest_driver(db, data)

    if not driver_id:
        return {"status": "no_driver_available"}

    return {
        "status": "assigned",
        "driver_id": driver_id
    }
