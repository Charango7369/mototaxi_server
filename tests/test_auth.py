import pytest
from fastapi import HTTPException
from app.auth import crear_token, verificar_token

def test_crear_token_retorna_string():
    assert isinstance(crear_token(1, 2), str)

def test_verificar_token_valido():
    payload = verificar_token(crear_token(5, 3))
    assert payload["driver_id"] == 5 and payload["sindicato_id"] == 3

def test_verificar_token_invalido_lanza_excepcion():
    with pytest.raises(HTTPException) as e:
        verificar_token("token.falso.invalido")
    assert e.value.status_code == 401

def test_verificar_token_manipulado():
    p = crear_token(1, 1).split(".")
    with pytest.raises(HTTPException) as e:
        verificar_token(p[0] + ".MANIPULADO." + p[2])
    assert e.value.status_code == 401
