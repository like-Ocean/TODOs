from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.websocket import manager

websocket_router = APIRouter(tags=["WebSocket"])


@websocket_router.websocket("/ws/tasks")
async def websocket_endpoint(websocket: WebSocket):
    client_id = await manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Подключение к WebSocket успешно установлено",
            "client_id": client_id
        })
        while True:
            data = await websocket.receive_text()

            await manager.broadcast({
                "type": "user_message",
                "client_id": client_id,
                "message": data,
                "timestamp": datetime.now().isoformat()
            })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        print(f"Клиент {client_id} отключился штатно")
    except Exception as e:
        print(f"WebSocket ошибка от {client_id}: {e}")
        manager.disconnect(client_id)
