import pytest
from app.assigner import distance, find_nearest_driver
from app.schemas import RideRequest

def test_distance_mismo_punto():
    assert distance(-14.5, -67.5, -14.5, -67.5) == pytest.approx(0.0, abs=1e-6)

def test_distance_valor_conocido():
    assert 220 < distance(-16.5, -68.15, -17.39, -66.16) < 250

def test_distance_simetrica():
    assert distance(-14.5,-67.5,-14.8,-67.3) == pytest.approx(distance(-14.8,-67.3,-14.5,-67.5), rel=1e-9)

def test_find_nearest_sin_conductores(db, sindicato):
    req = RideRequest(passenger_phone="60000000", origin_lat=-14.5, origin_lon=-67.5, sindicato_id=sindicato.id)
    assert find_nearest_driver(db, req, sindicato_id=sindicato.id) is None

def test_find_nearest_con_un_conductor(db, driver_aprobado, sindicato):
    req = RideRequest(passenger_phone="60000001", origin_lat=-14.5, origin_lon=-67.5, sindicato_id=sindicato.id)
    assert find_nearest_driver(db, req, sindicato_id=sindicato.id) == driver_aprobado.id

def test_find_nearest_elige_mas_cercano(db, sindicato):
    from app.models import Driver
    cerca = Driver(nombre="Cerca", telefono="70000041", sindicato_id=sindicato.id, lat=-14.5001, lon=-67.5001, estado="DISPONIBLE", estado_registro="APROBADO")
    lejos = Driver(nombre="Lejos", telefono="70000042", sindicato_id=sindicato.id, lat=-15.0, lon=-68.0, estado="DISPONIBLE", estado_registro="APROBADO")
    db.add_all([cerca, lejos]); db.commit()
    assert find_nearest_driver(db, RideRequest(passenger_phone="60000002", origin_lat=-14.5, origin_lon=-67.5)) == cerca.id

def test_find_nearest_ignora_conductores_ocupados(db, driver_aprobado):
    driver_aprobado.estado = "OCUPADO"; db.commit()
    assert find_nearest_driver(db, RideRequest(passenger_phone="60000003", origin_lat=-14.5, origin_lon=-67.5)) is None

def test_find_nearest_ignora_pendientes(db, sindicato):
    from app.models import Driver
    d = Driver(nombre="Pendiente", telefono="70000043", sindicato_id=sindicato.id, lat=-14.5, lon=-67.5, estado="DISPONIBLE", estado_registro="PENDIENTE")
    db.add(d); db.commit()
    assert find_nearest_driver(db, RideRequest(passenger_phone="60000004", origin_lat=-14.5, origin_lon=-67.5)) is None

def test_find_nearest_marca_conductor_ocupado(db, driver_aprobado):
    find_nearest_driver(db, RideRequest(passenger_phone="60000005", origin_lat=-14.5, origin_lon=-67.5))
    db.refresh(driver_aprobado)
    assert driver_aprobado.estado == "OCUPADO"
