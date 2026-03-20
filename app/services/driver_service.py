from sqlalchemy.orm import Session
from app.models import Driver

def get_all_drivers(db: Session):
    return db.query(Driver).all()