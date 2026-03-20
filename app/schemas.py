from pydantic import BaseModel

# -----------------------------
# UBICACIÓN DEL CONDUCTOR
# -----------------------------
class DriverLocation(BaseModel):
    driver_id: int
    lat: float
    lon: float


# -----------------------------
# SOLICITUD DE VIAJE
# -----------------------------
class RideRequest(BaseModel):
    lat: float
    lon: float
