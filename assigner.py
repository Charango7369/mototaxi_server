import sqlite3
import math

def distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1-lat2)**2 + (lon1-lon2)**2)

def find_nearest_driver(lat, lon):

    conn = sqlite3.connect("drivers.db")
    cur = conn.cursor()

    cur.execute("SELECT id, lat, lon FROM drivers WHERE estado='disponible'")

    drivers = cur.fetchall()

    conn.close()

    nearest_driver = None
    min_distance = 999999

    for d in drivers:

        d_id, d_lat, d_lon = d

        dist = distance(lat, lon, d_lat, d_lon)

        if dist < min_distance:
            min_distance = dist
            nearest_driver = d_id

    return nearest_driver
