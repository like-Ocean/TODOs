from fastapi import WebSocket
from typing import Dict
import uuid


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        client_id = str(uuid.uuid4())[:8]
        self.active_connections[client_id] = websocket
        print(f"Клиент {client_id} подключен. Всего: {len(self.active_connections)}")
        return client_id

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"Клиент {client_id} отключен. Осталось: {len(self.active_connections)}")

    async def broadcast(self, message: dict, exclude_client: str = None):
        disconnected = []

        for client_id, connection in list(self.active_connections.items()):
            if client_id == exclude_client:
                continue

            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Ошибка отправки клиенту {client_id}: {e}")
                disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(client_id)

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                print(f"Ошибка отправки клиенту {client_id}: {e}")
                self.disconnect(client_id)


manager = ConnectionManager()
