from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date

from app.database import get_db
from app.models import Ride, Driver

router = APIRouter(prefix="/monitor", tags=["Monitor"])


@router.get("/status")
def monitor_status(db: Session = Depends(get_db)):
    hoy = datetime.combine(date.today(), datetime.min.time())

    # Conductores online (con ubicación registrada)
    conductores_online = db.query(func.count(Driver.id))\
        .filter(Driver.estado.in_(["DISPONIBLE", "OCUPADO"]))\
        .scalar()

    # Viajes en curso ahora mismo
    viajes_en_curso = db.query(func.count(Ride.id))\
        .filter(Ride.status.in_(["ASIGNADO", "ACEPTADO", "EN_VIAJE"]))\
        .scalar()

    # Pedidos esperando conductor
    pedidos_esperando = db.query(func.count(Ride.id))\
        .filter(Ride.status == "ASIGNADO")\
        .scalar()

    # Finalizados hoy
    total_exito_hoy = db.query(func.count(Ride.id))\
        .filter(Ride.status == "FINALIZADO", Ride.created_at >= hoy)\
        .scalar()

    # Alerta crítica: más de 3 pedidos esperando sin conductor
    alerta_critica = pedidos_esperando > 3

    # Coordenadas de pedidos pendientes para el mapa
    pedidos_raw = db.query(Ride.origin_lat, Ride.origin_lon)\
        .filter(Ride.status == "ASIGNADO", Ride.created_at >= hoy)\
        .all()

    pedidos_coordenadas = [
        [r.origin_lat, r.origin_lon]
        for r in pedidos_raw
        if r.origin_lat and r.origin_lon
    ]

    # Ingresos del día
    ingresos_hoy = db.query(func.coalesce(func.sum(Ride.tarifa), 0))\
        .filter(Ride.status == "FINALIZADO", Ride.created_at >= hoy)\
        .scalar()

    return {
        "conductores_online":   conductores_online,
        "viajes_en_curso":      viajes_en_curso,
        "pedidos_esperando":    pedidos_esperando,
        "total_exito_hoy":      total_exito_hoy,
        "ingresos_hoy":         round(float(ingresos_hoy), 2),
        "alerta_critica":       alerta_critica,
        "pedidos_coordenadas":  pedidos_coordenadas,
        "timestamp":            datetime.now().isoformat(),
    }
