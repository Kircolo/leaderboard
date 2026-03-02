from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.cache.redis import close_redis
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import RequestIdMiddleware, configure_logging
from app.db.session import close_engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    yield
    await close_engine()
    await close_redis()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.add_middleware(RequestIdMiddleware)
    register_exception_handlers(application)
    application.include_router(api_router)
    return application


app = create_app()
