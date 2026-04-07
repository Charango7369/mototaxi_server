from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from starlette.websockets import WebSocketState
from app.websocket_manager import manager
import asyncio
import json

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/driver")
async def driver_channel(websocket: WebSocket, driver_id: int = Query(...)):
    # Aceptar sin validar Origin (necesario en Railway)
    await websocket.accept()
    manager.rooms.setdefault(driver_id, []).append(websocket)
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=15.0)
                try:
                    msg = json.loads(data)
                    if msg.get("event") == "ping":
                        await websocket.send_json({"event": "pong"})
                except Exception:
                    pass
            except asyncio.TimeoutError:
                await websocket.send_json({"event": "ping"})
    except WebSocketDisconnect:
        manager.disconnect_driver(driver_id, websocket)
    except Exception:
        manager.disconnect_driver(driver_id, websocket)


@router.websocket("/ws/operators")
async def operator_channel(websocket: WebSocket):
    # Aceptar sin validar Origin (necesario en Railway)
    await websocket.accept()
    manager.operators.append(websocket)
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=15.0)
                try:
                    msg = json.loads(data)
                    if msg.get("event") == "ping":
                        await websocket.send_json({"event": "pong"})
                except Exception:
                    pass
            except asyncio.TimeoutError:
                await websocket.send_json({"event": "ping"})
    except WebSocketDisconnect:
        manager.disconnect_operator(websocket)
    except Exception:
        manager.disconnect_operator(websocket)
