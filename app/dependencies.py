from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Driver


def get_current_driver(
    token: str = Header(...),
    db: Session = Depends(get_db)
):
    if not token.startswith("driver-"):
        raise HTTPException(status_code=401, detail="Token inválido")

    try:
        driver_id = int(token.split("-")[1])
    except:
        raise HTTPException(status_code=401, detail="Token mal formado")

    driver = db.query(Driver).filter(Driver.id == driver_id).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver no encontrado")

    return driver