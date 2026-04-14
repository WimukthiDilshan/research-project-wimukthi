from fastapi import FastAPI

from config.settings import settings
from routers import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
    )
    app.include_router(api_router, prefix=settings.API_PREFIX)
    return app


app = create_app()
