from fastapi import APIRouter, HTTPException
from core.background import task_manager
from core.websocket import manager

generator_router = APIRouter(prefix="/task-generator", tags=["Task Generator"])


@generator_router.post("/run")
async def run_task_generator():
    try:
        created_tasks = await task_manager.run_once()

        if not created_tasks:
            return {
                "status": "info",
                "message": "Новые задачи не созданы (возможно, все уже существуют или API недоступен)",
                "tasks": []
            }

        for task in created_tasks:
            await manager.broadcast({
                "type": "task_created",
                "data": {
                    "id": task.id,
                    "external_id": task.external_id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                }
            })

        return {
            "status": "success",
            "message": f"Успешно создано задач: {len(created_tasks)}",
            "tasks": [
                {
                    "id": task.id,
                    "external_id": task.external_id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                }
                for task in created_tasks
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@generator_router.post("/start")
async def start_task_generator():
    if task_manager.is_running:
        return {"status": "info", "message": "Генератор уже запущен"}

    await task_manager.start()
    return {"status": "success", "message": "Генератор задач запущен"}


@generator_router.post("/stop")
async def stop_task_generator():
    if not task_manager.is_running:
        return {"status": "info", "message": "Генератор уже остановлен"}

    await task_manager.stop()
    return {"status": "success", "message": "Генератор задач остановлен"}


@generator_router.get("/status")
async def get_task_generator_status():
    return {
        "is_running": task_manager.is_running,
        "interval_seconds": task_manager.interval,
        "api_url": task_manager.api_url,
        "current_offset": task_manager.current_offset
    }
