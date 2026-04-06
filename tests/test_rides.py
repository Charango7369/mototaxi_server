import pytest

@pytest.fixture
def ride_asignado(db, driver_aprobado, sindicato):
    from app.models import Ride
    r = Ride(driver_id=driver_aprobado.id, sindicato_id=sindicato.id,
        passenger_phone="60000001", origin_lat=-14.5, origin_lon=-67.5,
        destino="Mercado Central", tarifa=5.0, status="ASIGNADO")
    db.add(r); db.commit(); db.refresh(r)
    return r

class TestRequestRide:
    def test_sin_conductores_disponibles(self, client, sindicato):
        resp = client.post("/ride/request", json={"passenger_phone":"60000000","origin_lat":-14.5,"origin_lon":-67.5,"sindicato_id":sindicato.id})
        assert resp.json()["status"] == "no_driver_available"

    def test_asigna_conductor_disponible(self, client, driver_aprobado, sindicato):
        resp = client.post("/ride/request", json={"passenger_phone":"60000001","origin_lat":-14.5,"origin_lon":-67.5,"sindicato_id":sindicato.id})
        assert resp.json()["status"] == "assigned" and resp.json()["driver_id"] == driver_aprobado.id

    def test_conductor_queda_ocupado_tras_asignacion(self, client, db, driver_aprobado, sindicato):
        client.post("/ride/request", json={"passenger_phone":"60000002","origin_lat":-14.5,"origin_lon":-67.5,"sindicato_id":sindicato.id})
        db.refresh(driver_aprobado)
        assert driver_aprobado.estado == "OCUPADO"

    def test_segundo_viaje_sin_conductor(self, client, driver_aprobado, sindicato):
        client.post("/ride/request", json={"passenger_phone":"60000003","origin_lat":-14.5,"origin_lon":-67.5,"sindicato_id":sindicato.id})
        resp = client.post("/ride/request", json={"passenger_phone":"60000004","origin_lat":-14.5,"origin_lon":-67.5,"sindicato_id":sindicato.id})
        assert resp.json()["status"] == "no_driver_available"

class TestRidesActivos:
    def test_lista_viajes_activos(self, client, ride_asignado):
        ids = [r["ride_id"] for r in client.get("/ride/activos").json()]
        assert ride_asignado.id in ids

    def test_filtro_sindicato_sin_viajes(self, client, ride_asignado):
        assert client.get("/ride/activos?sindicato_id=9999").json() == []

class TestCancelRide:
    def test_cancelar_viaje(self, client, db, ride_asignado, driver_aprobado):
        assert client.post(f"/ride/{ride_asignado.id}/cancel").json()["status"] == "CANCELADO"
        db.refresh(driver_aprobado)
        assert driver_aprobado.estado == "DISPONIBLE"

    def test_cancelar_viaje_inexistente(self, client):
        assert client.post("/ride/9999/cancel").status_code == 404

    def test_cancelar_viaje_finalizado(self, client, db, ride_asignado):
        ride_asignado.status = "FINALIZADO"; db.commit()
        assert client.post(f"/ride/{ride_asignado.id}/cancel").status_code == 400

class TestAcceptStartFinish:
    def test_aceptar_viaje_sin_token(self, client, ride_asignado):
        assert client.post(f"/ride/{ride_asignado.id}/accept").status_code == 401

    def test_aceptar_viaje_de_otro_conductor(self, client, db, sindicato, ride_asignado):
        from app.models import Driver
        from app.auth import crear_token
        otro = Driver(nombre="Otro", telefono="70000099", sindicato_id=sindicato.id, estado="DISPONIBLE", estado_registro="APROBADO")
        db.add(otro); db.commit(); db.refresh(otro)
        resp = client.post(f"/ride/{ride_asignado.id}/accept", headers={"Authorization": f"Bearer {crear_token(otro.id, otro.sindicato_id)}"})
        assert resp.status_code == 403

    def test_flujo_completo(self, client, db, ride_asignado, token, driver_aprobado):
        for accion in ["accept", "start", "finish"]:
            assert client.post(f"/ride/{ride_asignado.id}/{accion}", headers={"Authorization": f"Bearer {token}"}).status_code == 200
        db.refresh(driver_aprobado)
        assert driver_aprobado.estado == "DISPONIBLE"
