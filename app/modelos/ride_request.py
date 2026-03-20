# app/modelos/ride_request.py
from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class RideRequest(Base):
    __tablename__ = "ride_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    origin_lat = Column(Float, nullable=False)
    origin_lon = Column(Float, nullable=False)
    dest_lat = Column(Float, nullable=False)
    dest_lon = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, accepted, completed
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)

    driver = relationship("Driver", back_populates="rides")