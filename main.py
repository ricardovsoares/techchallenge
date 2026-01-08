import os
import threading
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.configs import settings
from api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Estado e recursos inicializados no startup (igual ambiente real)
    app.state.tarefas_estado = {}
    app.state.tarefas_lock = threading.Lock()

    max_workers = int(os.getenv("MAX_WORKERS", "3"))
    app.state.executor = ThreadPoolExecutor(max_workers=max_workers)

    try:
        yield
    finally:
        # Garante liberação dos recursos no shutdown
        app.state.executor.shutdown(wait=False, cancel_futures=True)


def create_app() -> FastAPI:
    app = FastAPI(title="Catalogo de Livros", lifespan=lifespan)

    # CORS (recomendado: controlado por Config Vars no Render)
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app


app = create_app()
