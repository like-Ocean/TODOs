from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.websocket import manager
from typing import List
from service import task_service
from schemas.task import TaskCreate, TaskUpdate, TaskResponse

task_router = APIRouter(prefix="/task", tags=["TODOs"])


@task_router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks_endpoint(
        skip: int = 0, limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    tasks = await task_service.get_tasks(db, skip=skip, limit=limit)
    return tasks


@task_router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_endpoint(
        task_id: int, db: AsyncSession = Depends(get_db)
):
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


@task_router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_task_endpoint(
        task: TaskCreate,
        db: AsyncSession = Depends(get_db)
):
    new_task = await task_service.create_task(db, task)
    await manager.broadcast({
        "type": "task_created",
        "data": {
            "id": new_task.id,
            "title": new_task.title,
            "description": new_task.description,
            "completed": new_task.completed,
        }
    })

    return new_task


@task_router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task_endpoint(
        task_id: int, task_update: TaskUpdate,
        db: AsyncSession = Depends(get_db)
):
    updated_task = await task_service.update_task(db, task_id, task_update)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    await manager.broadcast({
        "type": "task_updated",
        "data": {
            "id": updated_task.id,
            "title": updated_task.title,
            "description": updated_task.description,
            "completed": updated_task.completed,
        }
    })

    return updated_task


@task_router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_endpoint(
        task_id: int,
        db: AsyncSession = Depends(get_db)
):
    success = await task_service.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    await manager.broadcast({
        "type": "task_deleted",
        "data": {"id": task_id}
    })

    return None
