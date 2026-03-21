from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "clave_por_defecto_cambiar")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", 10))


def crear_token(driver_id: int, sindicato_id: int) -> str:
    payload = {
        "driver_id":    driver_id,
        "sindicato_id": sindicato_id,
        "exp": datetime.utcnow() + timedelta(hours=EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("driver_id") is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expirado o inválido")
