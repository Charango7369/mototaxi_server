from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket_manager import manager
import asyncio

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/driver/{driver_id}")
async def driver_channel(websocket: WebSocket, driver_id: int):
    await manager.connect_driver(driver_id, websocket)
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=20.0)
            except asyncio.TimeoutError:
                # Ping cada 20s para mantener viva la conexion en Railway
                await websocket.send_json({"event": "ping"})
    except WebSocketDisconnect:
        manager.disconnect_driver(driver_id, websocket)
    except Exception:
        manager.disconnect_driver(driver_id, websocket)


@router.websocket("/ws/operators")
async def operator_channel(websocket: WebSocket):
    await manager.connect_operator(websocket)
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=20.0)
            except asyncio.TimeoutError:
                # Ping cada 20s para mantener viva la conexion en Railway
                await websocket.send_json({"event": "ping"})
    except WebSocketDisconnect:
        manager.disconnect_operator(websocket)
    except Exception:
        manager.disconnect_operator(websocket)
