# app/assigner.py
import math
from sqlalchemy.orm import Session
from app.models import Driver


def distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearest_driver(db: Session, ride_request, sindicato_id: int = None):
    query = db.query(Driver).filter(Driver.estado == "DISPONIBLE")

    if sindicato_id:
        query = query.filter(Driver.sindicato_id == sindicato_id)

    drivers = query.all()

    nearest = None
    min_dist = float("inf")

    for d in drivers:
        if d.lat is None or d.lon is None:
            continue
        dist = distance(ride_request.origin_lat, ride_request.origin_lon, d.lat, d.lon)
        if dist < min_dist:
            min_dist = dist
            nearest = d

    if not nearest:
        return None

    # ✅ Marcar como OCUPADO antes de devolver
    nearest.estado = "OCUPADO"
    db.commit()

    return nearest.id