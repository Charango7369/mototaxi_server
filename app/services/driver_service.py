from sqlalchemy.orm import Session
from app.models import Driver


def update_driver_location(db: Session, driver_id: int, lat: float, lon: float):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        return {"error": "Driver not found"}
    driver.lat = lat
    driver.lon = lon
    db.commit()
    return {"status": "updated"}
