from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    telefono = Column(String, unique=True)
    lat = Column(Float, default=0)
    lon = Column(Float, default=0)
    estado = Column(String, default="DISPONIBLE")


class Ride(Base):
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    passenger_lat = Column(Float)
    passenger_lon = Column(Float)
    status = Column(String, default="ASIGNADO")