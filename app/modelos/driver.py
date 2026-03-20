# app/modelos/driver.py
from sqlalchemy import Column, Integer, Float, String
from sqlalchemy.orm import relationship
from app.database import Base

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    status = Column(String, default="available")  # available, busy

    rides = relationship("RideRequest", back_populates="driver")