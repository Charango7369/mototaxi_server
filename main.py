from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sqlite3
import os
from models import DriverLocation, RideRequest
from assigner import find_nearest_driver
from database import init_db

app = FastAPI()

# Carpeta de páginas web
# app.mount("/web", StaticFiles(directory="web"), name="web")
# import os
# from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/web",
    StaticFiles(directory=os.path.join(BASE_DIR, "web")),
    name="web"
)
# Inicializar base de datos
init_db()


# -----------------------------
# ACTUALIZAR UBICACIÓN CONDUCTOR
# -----------------------------
@app.post("/driver/location")
def update_location(data: DriverLocation):

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute(
        "UPDATE drivers SET lat=?, lon=? WHERE id=?",
        (data.lat, data.lon, data.driver_id)
    )

    conn.commit()
    conn.close()

    return {"status": "location updated"}


# -----------------------------
# VER CONDUCTORES (para el mapa)
# -----------------------------
@app.get("/drivers")
def get_drivers():

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute("SELECT id, lat, lon FROM drivers")

    drivers = cur.fetchall()

    conn.close()

    return [
        {"id": d[0], "lat": d[1], "lon": d[2]}
        for d in drivers
    ]

# -----------------------------------------------
# PARA QUE EL CONDUCTOR CONSULTE VIAJES ASIGNADOS
# -----------------------------------------------
@app.get("/driver/{driver_id}/rides")
def get_driver_rides(driver_id: int):

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT id, passenger_lat, passenger_lon, status
    FROM rides
    WHERE driver_id=? AND status='ASIGNADO'
    """, (driver_id,))

    rides = cur.fetchall()

    conn.close()

    return [
        {
            "ride_id": r[0],
            "lat": r[1],
            "lon": r[2],
            "status": r[3]
        }
        for r in rides
    ]
# -----------------------------
# SOLICITAR VIAJE
# -----------------------------
@app.post("/ride/request")
def request_ride(ride: RideRequest):

    driver_id = find_nearest_driver(ride.lat, ride.lon)

    if driver_id is None:
        return {"status": "no drivers available"}

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO rides (driver_id, passenger_lat, passenger_lon, status)
        VALUES (?, ?, ?, ?)
    """, (driver_id, ride.lat, ride.lon, "ASIGNADO"))

    ride_id = cur.lastrowid

    conn.commit()
    conn.close()

    return {
        "ride_id": ride_id,
        "driver_id": driver_id,
        "status": "ASIGNADO"
    }


# -----------------------------
# VIAJES DE UN CONDUCTOR
# -----------------------------
@app.get("/driver/{driver_id}/rides")
def get_driver_rides(driver_id: int):

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT id, passenger_lat, passenger_lon, status
        FROM rides
        WHERE driver_id=? AND status='ASIGNADO'
    """, (driver_id,))

    rides = cur.fetchall()

    conn.close()

    return [
        {
            "ride_id": r[0],
            "lat": r[1],
            "lon": r[2],
            "status": r[3]
        }
        for r in rides
    ]


# -----------------------------
# ACTUALIZAR ESTADO DEL VIAJE
# -----------------------------
@app.post("/ride/{ride_id}/status")
def update_ride_status(ride_id: int, status: str):

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute(
        "UPDATE rides SET status=? WHERE id=?",
        (status, ride_id)
    )

    conn.commit()
    conn.close()

    return {"status": status}


@app.post("/driver/register")
def register_driver(nombre: str, telefono: str):

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO drivers (nombre, telefono, lat, lon, estado)
    VALUES (?, ?, ?, ?, ?)
    """, (nombre, telefono, 0, 0, "DISPONIBLE"))

    driver_id = cur.lastrowid

    conn.commit()
    conn.close()

    return {
        "driver_id": driver_id,
        "status": "registered"
    }

@app.post("/driver/login")
def driver_login(telefono: str):

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT id, nombre
    FROM drivers
    WHERE telefono=?
    """, (telefono,))

    driver = cur.fetchone()

    conn.close()

    if driver is None:
        return {"status": "not_found"}

    return {
        "status": "ok",
        "driver_id": driver[0],
        "nombre": driver[1]
    }

@app.get("/driver/{driver_id}/requests")
def driver_requests(driver_id: int):

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT id, passenger_lat, passenger_lon
    FROM rides
    WHERE driver_id=? AND status='ASIGNADO'
    """, (driver_id,))

    rides = cur.fetchall()

    conn.close()

    return [
        {
            "ride_id": r[0],
            "lat": r[1],
            "lon": r[2]
        }
        for r in rides
    ]

@app.post("/ride/request")
def request_ride(ride: RideRequest):

    driver_id = find_nearest_driver(ride.lat, ride.lon)

@app.post("/ride/{ride_id}/accept")
def accept_ride(ride_id: int):

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute("""
    UPDATE rides
    SET status='ACEPTADO'
    WHERE id=?
    """, (ride_id,))

    conn.commit()
    conn.close()

    return {"status": "ACEPTADO"}

@app.post("/ride/{ride_id}/start")
def start_ride(ride_id: int):

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute("""
    UPDATE rides
    SET status='EN_VIAJE'
    WHERE id=?
    """, (ride_id,))

    conn.commit()
    conn.close()

    return {"status": "EN_VIAJE"}

@app.post("/ride/{ride_id}/finish")
def finish_ride(ride_id: int):

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute("""
    UPDATE rides
    SET status='FINALIZADO'
    WHERE id=?
    """, (ride_id,))

    conn.commit()
    conn.close()

    return {"status": "FINALIZADO"}

