# app/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


# ─────────────────────────────────────────
# SINDICATO
# ─────────────────────────────────────────
class Sindicato(Base):
    __tablename__ = "sindicatos"

    id      = Column(Integer, primary_key=True, index=True)
    nombre  = Column(String, unique=True, nullable=False)  # "Sindicato 1" … "5"
    zona    = Column(String)                               # descripción de zona
    activo  = Column(Integer, default=1)                   # 1 = activo

    conductores = relationship("Driver", back_populates="sindicato")


# ─────────────────────────────────────────
# CONDUCTOR (MOTOTAXISTA)
# ─────────────────────────────────────────
class Driver(Base):
    __tablename__ = "drivers"

    id            = Column(Integer, primary_key=True, index=True)
    nombre        = Column(String, nullable=False)
    telefono      = Column(String, unique=True, nullable=False)
    placa         = Column(String, unique=True)
    sindicato_id  = Column(Integer, ForeignKey("sindicatos.id"), nullable=False)
    lat           = Column(Float, default=0.0)
    lon           = Column(Float, default=0.0)
    estado        = Column(String, default="DISPONIBLE")
    # DISPONIBLE | OCUPADO | INACTIVO

    sindicato = relationship("Sindicato", back_populates="conductores")
    viajes    = relationship("Ride", back_populates="conductor")


# ─────────────────────────────────────────
# VIAJE
# ─────────────────────────────────────────
class Ride(Base):
    __tablename__ = "rides"

    id             = Column(Integer, primary_key=True, index=True)
    driver_id      = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    sindicato_id   = Column(Integer, ForeignKey("sindicatos.id"), nullable=True)

    # Pasajero (por ahora identificado por teléfono, sin tabla propia)
    passenger_phone = Column(String, nullable=False)

    # Ubicaciones
    origin_lat  = Column(Float, nullable=False)
    origin_lon  = Column(Float, nullable=False)
    dest_lat    = Column(Float)
    dest_lon    = Column(Float)
    destino     = Column(String)   # nombre legible: "Mercado central"

    # Económico
    tarifa      = Column(Float, default=5.0)   # Bs.

    # Estado y tiempo
    status      = Column(String, default="PENDIENTE")
    # PENDIENTE | ASIGNADO | ACEPTADO | EN_VIAJE | FINALIZADO | CANCELADO
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    conductor = relationship("Driver", back_populates="viajes")