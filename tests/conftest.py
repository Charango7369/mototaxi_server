import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app

engine_test = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine_test)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_test)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def sindicato(db):
    from app.models import Sindicato
    s = Sindicato(nombre="Sindicato TEST", zona="ZONA TEST", activo=1)
    db.add(s); db.commit(); db.refresh(s)
    return s

@pytest.fixture
def driver_aprobado(db, sindicato):
    from app.models import Driver
    d = Driver(nombre="Juan Perez", telefono="70000001", placa="ABC-123",
        sindicato_id=sindicato.id, lat=-14.5, lon=-67.5,
        estado="DISPONIBLE", estado_registro="APROBADO")
    db.add(d); db.commit(); db.refresh(d)
    return d

@pytest.fixture
def token(driver_aprobado):
    from app.auth import crear_token
    return crear_token(driver_aprobado.id, driver_aprobado.sindicato_id)
