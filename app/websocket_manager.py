from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        # driver_id -> lista de conexiones (más robusto)
        self.rooms: Dict[int, List[WebSocket]] = {}

        # operadores conectados
        self.operators: List[WebSocket] = []

    # ─────────────────────────────
    # DRIVER
    # ─────────────────────────────
    async def connect_driver(self, driver_id: int, websocket: WebSocket):
        await websocket.accept()

        if driver_id not in self.rooms:
            self.rooms[driver_id] = []

        self.rooms[driver_id].append(websocket)

    def disconnect_driver(self, driver_id: int, websocket: WebSocket):
        if driver_id in self.rooms:
            if websocket in self.rooms[driver_id]:
                self.rooms[driver_id].remove(websocket)

            if not self.rooms[driver_id]:
                del self.rooms[driver_id]

    async def send_to_driver(self, driver_id: int, data: dict):
        connections = self.rooms.get(driver_id, [])

        dead = []
        for ws in connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect_driver(driver_id, ws)

    # ─────────────────────────────
    # OPERADORES
    # ─────────────────────────────
    async def connect_operator(self, websocket: WebSocket):
        await websocket.accept()
        self.operators.append(websocket)

    def disconnect_operator(self, websocket: WebSocket):
        if websocket in self.operators:
            self.operators.remove(websocket)

    async def broadcast_to_operators(self, data: dict):
        dead = []

        for ws in self.operators:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.operators.remove(ws)

    # ─────────────────────────────
    # 🔥 TIEMPO REAL (UBER MODE)
    # ─────────────────────────────
    async def broadcast_driver_location(self, driver_id: int, lat: float, lon: float):
        data = {
            "event": "driver_location",
            "driver_id": driver_id,
            "lat": lat,
            "lon": lon
        }

        await self.broadcast_to_operators(data)


# instancia global
manager = ConnectionManager()