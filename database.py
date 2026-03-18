import sqlite3

def init_db():

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        telefono TEXT,
        lat REAL,
        lon REAL,
        estado TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER,
        passenger_lat REAL,
        passenger_lon REAL,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()
