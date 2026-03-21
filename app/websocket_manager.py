from fastapi import WebSocket
from typing import Dict


class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[int, WebSocket] = {}
        self.operators: list[WebSocket] = []

    async def connect_driver(self, driver_id: int, websocket: WebSocket):
        await websocket.accept()
        self.rooms[driver_id] = websocket

    def disconnect_driver(self, driver_id: int):
        self.rooms.pop(driver_id, None)

    async def send_to_driver(self, driver_id: int, data: dict):
        ws = self.rooms.get(driver_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect_driver(driver_id)

    async def connect_operator(self, websocket: WebSocket):
        await websocket.accept()
        self.operators.append(websocket)

    def disconnect_operator(self, websocket: WebSocket):
        if websocket in self.operators:
            self.operators.remove(websocket)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.operators:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.operators.remove(ws)


manager = ConnectionManager()
