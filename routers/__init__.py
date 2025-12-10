from .task import task_route
from .generator import generator_route
from .websocket import websocket_route


routes = [
    task_route.task_router,
    generator_route.generator_router,
    websocket_route.websocket_router
]
