import asyncio
import httpx
from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.task import Task


class BackgroundTaskManager:
    def __init__(self):
        self.task: asyncio.Task = None
        self.is_running = False
        self.interval = 120
        self.api_url = "https://dummyjson.com/todos"
        self.current_skip = 0
        self.batch_size = 5

    async def fetch_external_tasks(self) -> list[dict]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                params = {
                    'limit': self.batch_size,
                    'skip': self.current_skip
                }
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()
                if not response.text:
                    return []

                data = response.json()
                todos = data.get('todos', [])
                total = data.get('total', 0)

                self.current_skip += self.batch_size

                if self.current_skip >= total:
                    self.current_skip = 0

                return todos

        except httpx.TimeoutException:
            print(f"Timeout при запросе к {self.api_url}")
            return []
        except httpx.HTTPStatusError as e:
            print(f"HTTP ошибка {e.response.status_code}: {e.response.text[:200]}")
            return []
        except ValueError as e:
            print(f"Ошибка ответ сервера: {response.text[:500] if 'response' in locals() else 'N/A'}")
            return []
        except Exception as e:
            print(f"Неожиданная ошибка: {type(e).__name__}: {e}")
            return []

    async def check_task_exists(self, session, external_id: int) -> bool:
        result = await session.execute(
            select(Task).where(Task.external_id == external_id)
        )
        return result.scalar_one_or_none() is not None

    def convert_todo_to_task_data(self, todo: dict) -> dict:
        return {
            'external_id': todo['id'],
            'title': todo['todo'][:200],
            'description': f"Импортировано из DummyJSON API | User ID: {todo.get('userId', 'N/A')}",
            'completed': todo.get('completed', False)
        }

    async def generate_task(self):
        external_todos = await self.fetch_external_tasks()

        if not external_todos:
            return []

        created_tasks = []
        async with AsyncSessionLocal() as session:
            for todo in external_todos:
                try:
                    exists = await self.check_task_exists(session, todo['id'])
                    if exists:
                        continue

                    task_data = self.convert_todo_to_task_data(todo)
                    new_task = Task(**task_data)

                    session.add(new_task)
                    await session.commit()
                    await session.refresh(new_task)

                    created_tasks.append(new_task)

                    status_icon = "✅" if new_task.completed else "⬜"
                    print(
                        f"{status_icon} Создана задача: [API#{new_task.external_id}] {new_task.title[:50]}... (DB#{new_task.id})")

                except KeyError as e:
                    print(f"Отсутствует поле в TODO: {e}")
                    continue
                except Exception as e:
                    print(f"Ошибка создания задачи: {e}")
                    await session.rollback()
                    continue

        return created_tasks

    async def periodic_task(self):
        while self.is_running:
            try:
                created_tasks = await self.generate_task()
                if created_tasks:
                    from core.websocket import manager
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
                    print(f"Создано задач: {len(created_tasks)}")
                else:
                    print("Новых задач не создано")

            except Exception as e:
                print(f"Ошибка в periodic_task: {e}")

            await asyncio.sleep(self.interval)

    async def start(self):
        if not self.is_running:
            self.is_running = True
            self.task = asyncio.create_task(self.periodic_task())
            print(f"Фоновая задача запущена")
            print(f"API: {self.api_url}")
            print(f"Интервал: {self.interval}с")
            print(f"Порция: {self.batch_size} задач")

    async def stop(self):
        if self.is_running:
            self.is_running = False
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            print("Фоновая задача остановлена")

    async def run_once(self):
        created_tasks = await self.generate_task()
        return created_tasks if created_tasks else []


task_manager = BackgroundTaskManager()
