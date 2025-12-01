from fastapi import FastAPI, BackgroundTasks, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
from utils.gerar_aquivo import salvar_em_excel
from utils.configs import settings
from scripts.web_scraping_api import WebScraperComPaginacao, executar_scraper_background
from models.scraping_model import ConfiguracaoScraper, RespostaExecucao
from fastapi.middleware.cors import CORSMiddleware
import uuid
import threading
from utils.estado import (
    tarefas_estado,
    tarefas_lock,
    criar_tarefa,
    obter_tarefa,
    obter_todas_tarefas,
    limpar_concluidas
)
router_scraping = APIRouter()


@router_scraping.post("/iniciar", response_model=RespostaExecucao)
async def iniciar_scraper(config: ConfiguracaoScraper, background_tasks: BackgroundTasks):
    """
    Inicia uma nova tarefa de scraping.

    **Exemplo de uso:**
    ```json
    {
        "url_inicial": "https://books.toscrape.com/index.html",
        "section_selector": "section",
        "li_selector": "li.col-xs-6.col-sm-4.col-md-3.col-lg-3",
        "next_page_selector": "ul.pager li.next a",
        "max_paginas": 5,
        "salvar_excel": true
    }
    ```
    """
    tarefa_id = str(uuid.uuid4())
    criar_tarefa(tarefa_id)

    print(f"📝 ID da tarefa: {tarefa_id}")
    print(f"📊 Total de tarefas: {len(obter_todas_tarefas())}\n")

    background_tasks.add_task(
        executar_scraper_background,
        tarefa_id,
        config
    )

    return {
        "tarefa_id": tarefa_id,
        "status": "iniciado",
        "mensagem": "Scraping iniciado em background. Use o tarefa_id para monitorar progresso."
    }


@router_scraping.get("/status/{tarefa_id}")
async def obter_status(tarefa_id: str):
    """Obtém status de uma tarefa"""
    tarefa = obter_tarefa(tarefa_id)

    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    return {
        "tarefa_id": tarefa_id,
        **tarefa,

        "total_produtos": len(tarefa["resultados"]) if tarefa["resultados"] else 0
    }


@router_scraping.get("/resultados/{tarefa_id}")
async def obter_resultados(tarefa_id: str):
    """Obtém resultados de uma tarefa"""
    tarefa = obter_tarefa(tarefa_id)

    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    if tarefa["status"] != "concluido":
        raise HTTPException(
            status_code=400, detail=f"Tarefa em {tarefa['status']}")

    return {
        "tarefa_id": tarefa_id,
        "total_produtos": len(tarefa["resultados"])
        # "produtos": tarefa["resultados"]
    }


@router_scraping.get("/listar-tarefas")
async def listar_tarefas():
    """Lista TODAS as tarefas"""
    print(f"\n📋 Listando tarefas...")

    todas_tarefas = obter_todas_tarefas()

    print(f"Total: {len(todas_tarefas)}\n")

    if not todas_tarefas:
        return {
            "total_tarefas": 0,
            "mensagem": "Nenhuma tarefa registrada",
            "resumo": {"em_progresso": 0, "concluido": 0, "erro": 0, "aguardando": 0},
            "tarefas": {}
        }

    tarefas_resumo = {}
    for tid, info in todas_tarefas.items():
        tarefas_resumo[tid] = {
            "status": info["status"],
            "progresso": info.get("progresso", 0),
            "mensagem": info.get("mensagem", ""),
            "total_produtos": len(info["resultados"]) if info["resultados"] else 0,
            "erro": info.get("erro"),
            "timestamp_criacao": info.get("timestamp_criacao")
        }

    contadores = {
        "em_progresso": sum(1 for t in tarefas_resumo.values() if t["status"] == "progresso"),
        "concluido": sum(1 for t in tarefas_resumo.values() if t["status"] == "concluido"),
        "erro": sum(1 for t in tarefas_resumo.values() if t["status"] == "erro"),
        "aguardando": sum(1 for t in tarefas_resumo.values() if t["status"] == "aguardando")
    }

    return {
        "total_tarefas": len(todas_tarefas),
        "resumo": contadores,
        "tarefas": tarefas_resumo
    }


@router_scraping.get("/scraper/listar-tarefas-detalhado", tags=["Scraper"])
async def listar_tarefas_detalhado():
    """Lista tarefas detalhado"""
    todas_tarefas = obter_todas_tarefas()

    if not todas_tarefas:
        return {"total_tarefas": 0, "tarefas": []}

    tarefas_lista = []
    for tid, info in todas_tarefas.items():
        tarefas_lista.append({
            "tarefa_id": tid,
            "status": info["status"],
            "total_produtos": len(info["resultados"]) if info["resultados"] else 0,
            "primeiros_5": [
                {"titulo": p.get("titulo", "")[
                    :60], "preco": p.get("preco", "")}
                for p in (info["resultados"][:5] if info["resultados"] else [])
            ]
        })

    return {"total_tarefas": len(todas_tarefas), "tarefas": tarefas_lista}


@router_scraping.delete("/scraper/limpar-tarefas", tags=["Scraper"])
async def limpar_tarefas_endpoint():
    """Limpa tarefas concluídas"""
    limpas = limpar_concluidas()
    todas_tarefas = obter_todas_tarefas()

    return {
        "limpas": limpas,
        "restantes": len(todas_tarefas)
    }


@router_scraping.get("/health")
async def health_check():
    """
    Health check para verificar se a API está rodando.
    """
    return {"status": "ok", "servico": "Web Scraper API"}
