from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from core.database import engine, Base
from core.config import settings
from core.background import task_manager
from routers import routes

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENV == "development" or settings.ENV == "production":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created")

    await task_manager.start()

    print("Application started successfully")

    yield

    await task_manager.stop()
    await engine.dispose()
    print("Application stopped")


app = FastAPI(
    title="TODOs API + WebSocket",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routes:
    app.include_router(router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_RELOAD,
        log_level=settings.APP_LOG_LEVEL.lower()
    )
