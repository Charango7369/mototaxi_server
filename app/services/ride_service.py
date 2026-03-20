from app.models import Ride

# -----------------------------
# ACTUALIZAR ESTADO CON VALIDACIÓN
# -----------------------------
def update_ride_status(db, ride_id: int, new_status: str):

    ride = db.query(Ride).filter(Ride.id == ride_id).first()

    if not ride:
        return {"error": "ride not found"}

    valid_transitions = {
        "ASIGNADO": ["ACEPTADO"],
        "ACEPTADO": ["EN_VIAJE"],
        "EN_VIAJE": ["FINALIZADO"]
    }

    current_status = ride.status

    if current_status not in valid_transitions:
        return {"error": f"estado inválido actual: {current_status}"}

    if new_status not in valid_transitions[current_status]:
        return {
            "error": f"no puedes pasar de {current_status} a {new_status}"
        }

    ride.status = new_status
    db.commit()

    return {"status": new_status}
