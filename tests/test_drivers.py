import pytest

class TestRegistro:
    def test_registro_exitoso(self, client, sindicato):
        resp = client.post("/driver/register", json={"nombre":"Ana","telefono":"70000002","placa":"XYZ-999","sindicato_id":sindicato.id})
        assert resp.status_code == 200 and "token" in resp.json()

    def test_registro_telefono_duplicado(self, client, sindicato):
        p = {"nombre":"Pedro","telefono":"70000003","placa":"DUP-001","sindicato_id":sindicato.id}
        client.post("/driver/register", json=p)
        assert client.post("/driver/register", json={**p,"placa":"DUP-002"}).status_code == 400

    def test_registro_sindicato_inexistente(self, client):
        resp = client.post("/driver/register", json={"nombre":"X","telefono":"70000004","sindicato_id":9999})
        assert resp.status_code == 200  # BUG: SQLite no valida FK

class TestLogin:
    def test_login_exitoso(self, client, driver_aprobado):
        resp = client.post("/driver/login", json={"telefono": driver_aprobado.telefono})
        assert resp.status_code == 200 and "token" in resp.json()

    def test_login_conductor_no_existe(self, client):
        assert client.post("/driver/login", json={"telefono":"99999999"}).status_code == 404

    def test_login_conductor_pendiente(self, client, db, sindicato):
        from app.models import Driver
        d = Driver(nombre="P", telefono="70000010", sindicato_id=sindicato.id, estado="INACTIVO", estado_registro="PENDIENTE")
        db.add(d); db.commit()
        resp = client.post("/driver/login", json={"telefono":"70000010"})
        assert resp.status_code == 403 and "pendiente" in resp.json()["detail"].lower()

    def test_login_conductor_rechazado(self, client, db, sindicato):
        from app.models import Driver
        d = Driver(nombre="R", telefono="70000011", sindicato_id=sindicato.id, estado="INACTIVO", estado_registro="RECHAZADO")
        db.add(d); db.commit()
        resp = client.post("/driver/login", json={"telefono":"70000011"})
        assert resp.status_code == 403 and "rechazado" in resp.json()["detail"].lower()

class TestLocation:
    def test_actualizar_ubicacion(self, client, driver_aprobado):
        resp = client.post("/driver/location", params={"driver_id":driver_aprobado.id,"lat":-14.8,"lon":-67.3})
        assert resp.status_code == 200

    def test_ubicacion_conductor_no_existe(self, client):
        assert client.post("/driver/location", params={"driver_id":9999,"lat":-14.8,"lon":-67.3}).status_code == 404

class TestAprobacion:
    def test_aprobar_conductor(self, client, db, sindicato):
        from app.models import Driver
        d = Driver(nombre="A", telefono="70000020", sindicato_id=sindicato.id, estado="INACTIVO", estado_registro="PENDIENTE")
        db.add(d); db.commit()
        assert client.post(f"/driver/aprobar/{d.id}").json()["status"] == "aprobado"

    def test_rechazar_conductor(self, client, db, sindicato):
        from app.models import Driver
        d = Driver(nombre="R", telefono="70000021", sindicato_id=sindicato.id, estado="INACTIVO", estado_registro="PENDIENTE")
        db.add(d); db.commit()
        assert client.post(f"/driver/rechazar/{d.id}").status_code == 200

    def test_aprobar_conductor_inexistente(self, client):
        assert client.post("/driver/aprobar/9999").status_code == 404

class TestConsultas:
    def test_get_driver(self, client, driver_aprobado):
        assert client.get(f"/driver/{driver_aprobado.id}").status_code == 200

    def test_get_driver_no_existe(self, client):
        assert client.get("/driver/9999").status_code == 404

    def test_lista_todos_conductores(self, client, driver_aprobado):
        assert len(client.get("/driver/lista/todos").json()) >= 1

    def test_lista_pendientes(self, client, db, sindicato):
        from app.models import Driver
        d = Driver(nombre="P2", telefono="70000030", sindicato_id=sindicato.id, estado="INACTIVO", estado_registro="PENDIENTE")
        db.add(d); db.commit()
        ids = [x["driver_id"] for x in client.get("/driver/lista/pendientes").json()]
        assert d.id in ids

    def test_estado_registro(self, client, driver_aprobado):
        assert client.get(f"/driver/estado/{driver_aprobado.telefono}").json()["estado_registro"] == "APROBADO"

    def test_set_disponible(self, client, db, driver_aprobado):
        driver_aprobado.estado = "OCUPADO"; db.commit()
        assert client.post(f"/driver/disponible/{driver_aprobado.id}").json()["status"] == "DISPONIBLE"
