import math
from sqlalchemy.orm import Session
from app.models import Driver


# -----------------------------
# DISTANCIA (HAVERSINE)
# -----------------------------
def distance(lat1, lon1, lat2, lon2):
    R = 6371  # km

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# -----------------------------
# BUSCAR CONDUCTOR MÁS CERCANO
# -----------------------------
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
