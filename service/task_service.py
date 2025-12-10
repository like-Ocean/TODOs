from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from models import Task
from schemas.task import TaskCreate, TaskUpdate


async def get_tasks(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Task]:
    result = await db.execute(select(Task).offset(skip).limit(limit).order_by(Task.id))
    return list(result.scalars().all())


async def get_task(db: AsyncSession, task_id: int) -> Optional[Task]:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def create_task(db: AsyncSession, task: TaskCreate) -> Task:
    db_task = Task(**task.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


async def update_task(db: AsyncSession, task_id: int, task_update: TaskUpdate) -> Optional[Task]:
    db_task = await get_task(db, task_id)
    if not db_task:
        return None

    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    await db.commit()
    await db.refresh(db_task)
    return db_task


async def delete_task(db: AsyncSession, task_id: int):
    db_task = await get_task(db, task_id)
    if not db_task:
        return False

    await db.delete(db_task)
    await db.commit()
    return True
