from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket_manager import manager

router = APIRouter(tags=["WebSocket"])


# ─────────────────────────────
# DRIVER (envía ubicación)
# ─────────────────────────────
@router.websocket("/ws/driver/{driver_id}")
async def driver_channel(websocket: WebSocket, driver_id: int):
    await manager.connect_driver(driver_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            # 🔥 ubicación en tiempo real
            if data.get("type") == "location":
                await manager.broadcast_driver_location(
                    driver_id,
                    data["lat"],
                    data["lon"]
                )

    except WebSocketDisconnect:
        manager.disconnect_driver(driver_id, websocket)


# ─────────────────────────────
# OPERADOR (solo recibe)
# ─────────────────────────────
@router.websocket("/ws/operators")
async def operator_channel(websocket: WebSocket):
    await manager.connect_operator(websocket)

    try:
        while True:
            # mantener conexión viva
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect_operator(websocket)
    
    