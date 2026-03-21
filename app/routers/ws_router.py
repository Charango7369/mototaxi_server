from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket_manager import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/driver/{driver_id}")
async def driver_channel(websocket: WebSocket, driver_id: int):
    await manager.connect_driver(driver_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_driver(driver_id)


@router.websocket("/ws/operators")
async def operator_channel(websocket: WebSocket):
    await manager.connect_operator(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_operator(websocket)
