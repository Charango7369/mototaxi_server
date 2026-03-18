from pydantic import BaseModel

class DriverLocation(BaseModel):
    driver_id: int
    lat: float
    lon: float


class RideRequest(BaseModel):
    lat: float
    lon: float
