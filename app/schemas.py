# app/schemas.py
from pydantic import BaseModel
from typing import Optional


class DriverLocation(BaseModel):
    driver_id: int
    lat: float
    lon: float


class RideRequest(BaseModel):
    passenger_phone: str
    origin_lat: float
    origin_lon: float
    dest_lat: Optional[float] = None
    dest_lon: Optional[float] = None
    destino: Optional[str] = None
    sindicato_id: Optional[int] = None
    tarifa: Optional[float] = 5.0