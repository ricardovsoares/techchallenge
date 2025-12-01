from fastapi import FastAPI
from utils.configs import settings
from api.v1.api import api_router
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
import threading

app = FastAPI(title='Catalogo de Livros')
# Adicionar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tarefas_estado: Dict = {}
executor = ThreadPoolExecutor(max_workers=3)
tarefas_lock = threading.Lock()

app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000,
                log_level="info", reload=True)
