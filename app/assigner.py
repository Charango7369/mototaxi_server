from sqlalchemy.orm import Session
from app.models import Driver
import math


def distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)


def find_nearest_driver(db: Session, ride_request):
    drivers = db.query(Driver).filter(Driver.estado == "DISPONIBLE").all()

    nearest_driver = None
    min_distance = float("inf")

    for d in drivers:
        if d.lat is None or d.lon is None:
            continue

        dist = distance(ride_request.lat, ride_request.lon, d.lat, d.lon)

        if dist < min_distance:
            min_distance = dist
            nearest_driver = d

    return nearest_driver.id if nearest_driver else None