from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, date
from typing import Optional

from app.database import get_db
from app.models import Ride, Driver, Sindicato

router = APIRouter(prefix="/stats", tags=["Estadísticas"])


# ─────────────────────────────────────────
# HELPER: rango de fechas
# ─────────────────────────────────────────
def rango(periodo: str) -> datetime:
    hoy = date.today()
    if periodo == "dia":
        inicio = hoy
    elif periodo == "semana":
        inicio = hoy - timedelta(days=hoy.weekday())
    elif periodo == "mes":
        inicio = hoy.replace(day=1)
    else:
        inicio = hoy
    return datetime.combine(inicio, datetime.min.time())


# ─────────────────────────────────────────
# RESUMEN GENERAL — 3 queries agregadas
# ─────────────────────────────────────────
@router.get("/resumen")
def resumen_general(
    periodo: str = Query("dia", enum=["dia", "semana", "mes"]),
    sindicato_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    desde = rango(periodo)

    filtros = [Ride.created_at >= desde]
    if sindicato_id:
        filtros.append(Ride.sindicato_id == sindicato_id)

    # Query 1: totales por status en una sola pasada
    por_status = db.query(
        Ride.status,
        func.count(Ride.id).label("total")
    ).filter(*filtros).group_by(Ride.status).all()

    conteo = {row.status: row.total for row in por_status}
    total  = sum(conteo.values())

    # Query 2: ingresos solo de finalizados
    ingresos_row = db.query(
        func.count(Ride.id).label("n"),
        func.coalesce(func.sum(Ride.tarifa), 0).label("total_bs")
    ).filter(*filtros, Ride.status == "FINALIZADO").one()

    finalizados = ingresos_row.n
    total_bs    = float(ingresos_row.total_bs)
    promedio    = round(total_bs / finalizados, 2) if finalizados > 0 else 0

    en_curso = sum(
        conteo.get(s, 0) for s in ("ASIGNADO", "ACEPTADO", "EN_VIAJE")
    )

    return {
        "periodo":         periodo,
        "desde":           desde.isoformat(),
        "total_viajes":    total,
        "finalizados":     finalizados,
        "en_curso":        en_curso,
        "cancelados":      conteo.get("CANCELADO", 0),
        "ingresos_total":  round(total_bs, 2),
        "tarifa_promedio": promedio,
    }


# ─────────────────────────────────────────
# CONDUCTORES — 1 query con JOIN + GROUP BY
# ─────────────────────────────────────────
@router.get("/conductores")
def stats_conductores(
    periodo: str = Query("dia", enum=["dia", "semana", "mes"]),
    sindicato_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    desde = rango(periodo)

    q = db.query(
        Driver.id,
        Driver.nombre,
        Driver.placa,
        Driver.sindicato_id,
        func.count(Ride.id).label("viajes"),
        func.coalesce(func.sum(Ride.tarifa), 0).label("ingresos")
    ).join(Ride, and_(
        Ride.driver_id == Driver.id,
        Ride.created_at >= desde,
        Ride.status == "FINALIZADO"
    ), isouter=True)

    if sindicato_id:
        q = q.filter(Driver.sindicato_id == sindicato_id)

    rows = q.group_by(Driver.id)\
            .order_by(func.count(Ride.id).desc())\
            .all()

    return [
        {
            "driver_id":    r.id,
            "nombre":       r.nombre,
            "placa":        r.placa or "—",
            "sindicato_id": r.sindicato_id,
            "viajes":       r.viajes,
            "ingresos":     round(float(r.ingresos), 2),
            "promedio":     round(float(r.ingresos) / r.viajes, 2) if r.viajes > 0 else 0
        }
        for r in rows
    ]


# ─────────────────────────────────────────
# SINDICATOS — 1 query con OUTER JOIN
# ─────────────────────────────────────────
@router.get("/sindicatos")
def stats_sindicatos(
    periodo: str = Query("dia", enum=["dia", "semana", "mes"]),
    db: Session = Depends(get_db)
):
    desde = rango(periodo)

    # Total viajes por sindicato
    totales = db.query(
        Ride.sindicato_id,
        func.count(Ride.id).label("total")
    ).filter(Ride.created_at >= desde)     .group_by(Ride.sindicato_id).all()

    # Finalizados e ingresos por sindicato
    finales = db.query(
        Ride.sindicato_id,
        func.count(Ride.id).label("n"),
        func.coalesce(func.sum(Ride.tarifa), 0).label("bs")
    ).filter(Ride.created_at >= desde, Ride.status == "FINALIZADO")     .group_by(Ride.sindicato_id).all()

    tot_map = {r.sindicato_id: r.total for r in totales}
    fin_map = {r.sindicato_id: {"n": r.n, "bs": float(r.bs)} for r in finales}

    sindicatos = db.query(Sindicato).order_by(Sindicato.id).all()

    return [
        {
            "sindicato_id": s.id,
            "nombre":       s.nombre,
            "zona":         s.zona,
            "total_viajes": tot_map.get(s.id, 0),
            "finalizados":  fin_map.get(s.id, {}).get("n", 0),
            "ingresos":     round(fin_map.get(s.id, {}).get("bs", 0.0), 2),
        }
        for s in sindicatos
    ]


# ─────────────────────────────────────────
# HISTORIAL — query filtrada y paginada
# ─────────────────────────────────────────
@router.get("/historial")
def historial_viajes(
    periodo:      str = Query("dia", enum=["dia", "semana", "mes"]),
    sindicato_id: Optional[int] = None,
    driver_id:    Optional[int] = None,
    status:       Optional[str] = None,
    limit:        int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    desde = rango(periodo)

    # JOIN con Driver para traer nombre y placa en una sola query
    q = db.query(
        Ride.id,
        Ride.driver_id,
        Ride.sindicato_id,
        Ride.passenger_phone,
        Ride.destino,
        Ride.tarifa,
        Ride.status,
        Ride.created_at,
        Driver.nombre.label("driver_nombre"),
        Driver.placa.label("driver_placa"),
    ).outerjoin(Driver, Driver.id == Ride.driver_id)\
     .filter(Ride.created_at >= desde)

    if sindicato_id:
        q = q.filter(Ride.sindicato_id == sindicato_id)
    if driver_id:
        q = q.filter(Ride.driver_id == driver_id)
    if status:
        q = q.filter(Ride.status == status.upper())

    rows = q.order_by(Ride.created_at.desc()).limit(limit).all()

    return [
        {
            "ride_id":        r.id,
            "driver_id":      r.driver_id,
            "driver_nombre":  r.driver_nombre or "—",
            "driver_placa":   r.driver_placa  or "—",
            "sindicato_id":   r.sindicato_id,
            "passenger_phone": r.passenger_phone,
            "destino":        r.destino,
            "tarifa":         r.tarifa,
            "status":         r.status,
            "created_at":     r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


# ─────────────────────────────────────────
# POR HORA — GROUP BY hora con func.strftime
# ─────────────────────────────────────────
@router.get("/por-hora")
def viajes_por_hora(
    fecha:        Optional[str] = None,
    sindicato_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    if fecha:
        dia = datetime.strptime(fecha, "%Y-%m-%d").date()
    else:
        dia = date.today()

    inicio = datetime.combine(dia, datetime.min.time())
    fin    = inicio + timedelta(days=1)

    filtros = [Ride.created_at >= inicio, Ride.created_at < fin]
    if sindicato_id:
        filtros.append(Ride.sindicato_id == sindicato_id)

    # SQLite: strftime('%H', ...) devuelve la hora como string "00".."23"
    hora_col = func.strftime("%H", Ride.created_at)

    # Totales por hora
    totales_hora = db.query(
        hora_col.label("hora"),
        func.count(Ride.id).label("total")
    ).filter(*filtros).group_by(hora_col).all()

    # Finalizados e ingresos por hora
    finales_hora = db.query(
        hora_col.label("hora"),
        func.count(Ride.id).label("n"),
        func.coalesce(func.sum(Ride.tarifa), 0).label("bs")
    ).filter(*filtros, Ride.status == "FINALIZADO")     .group_by(hora_col).all()

    tot_h = {r.hora: r.total for r in totales_hora}
    fin_h = {r.hora: {"n": r.n, "bs": float(r.bs)} for r in finales_hora}

    rows = [(h,) for h in tot_h]  # placeholder para el loop siguiente

    return [
        {
            "hora":        h,
            "label":       f"{h:02d}:00",
            "total":       tot_h.get(f"{h:02d}", 0),
            "finalizados": fin_h.get(f"{h:02d}", {}).get("n", 0),
            "ingresos":    fin_h.get(f"{h:02d}", {}).get("bs", 0.0)
        }
        for h in range(24)
    ]


# ─────────────────────────────────────────
# DESTINOS — GROUP BY destino
# ─────────────────────────────────────────
@router.get("/destinos")
def destinos_frecuentes(
    periodo:      str = Query("semana", enum=["dia", "semana", "mes"]),
    sindicato_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    desde = rango(periodo)

    filtros = [
        Ride.created_at >= desde,
        Ride.destino != None,
        Ride.destino != ""
    ]
    if sindicato_id:
        filtros.append(Ride.sindicato_id == sindicato_id)

    rows = db.query(
        Ride.destino,
        func.count(Ride.id).label("viajes"),
        func.coalesce(func.sum(Ride.tarifa), 0).label("ingresos")
    ).filter(*filtros)\
     .group_by(Ride.destino)\
     .order_by(func.count(Ride.id).desc())\
     .limit(10)\
     .all()

    return [
        {
            "destino":  r.destino.strip().title(),
            "viajes":   r.viajes,
            "ingresos": round(float(r.ingresos), 2)
        }
        for r in rows
    ]
