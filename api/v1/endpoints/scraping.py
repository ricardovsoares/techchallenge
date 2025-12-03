from fastapi import BackgroundTasks, HTTPException, APIRouter, status
from datetime import datetime

from selenium.webdriver.support import expected_conditions as EC


from utils.configs import settings
from scripts.web_scraping_api import executar_scraper_background
from models.scraping_model import ConfiguracaoScraper, RespostaExecucao
from fastapi.middleware.cors import CORSMiddleware
import uuid
from utils.estado import (
    tarefas_estado,
    tarefas_lock,
    criar_tarefa,
    obter_tarefa,
    obter_todas_tarefas,
    limpar_concluidas
)
from utils.auth import verifica_token, TokenData
from fastapi import Depends
from utils.logger import configura_logger


logger = configura_logger(__name__, "scraping.log")

router_scraping = APIRouter()


@router_scraping.post("/iniciar", response_model=RespostaExecucao, dependencies=[Depends(verifica_token)], summary="🚀 Iniciar Nova Tarefa de Scraping",
                      tags=["Scraper"],
                      responses={
                          202: {
                              "description": "Tarefa criada com sucesso e adicionada à fila de processamento",
                              "content": {
                                  "application/json": {
                                      "example": {
                                          "tarefa_id": "550e8400-e29b-41d4-a716-446655440000",
                                          "status": "iniciado",
                                          "mensagem": "Scraping iniciado em background. Use o tarefa_id para monitorar progresso.",
                                          "timestamp": "2025-03-12T14:30:45.123456"
                                      }
                                  }
                              }
                          },
                          401: {
                              "description": "Erro de autenticação - Token inválido ou ausente",

                          },
                          422: {
                              "description": "Erro de validação - Dados de entrada inválidos",

                          },
                          500: {
                              "description": "Erro interno do servidor",
                          }})
async def iniciar_scraper(config: ConfiguracaoScraper, background_tasks: BackgroundTasks, usuario_atual: TokenData = Depends(verifica_token)):
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
    try:
        logger.info(
            f"Iniciando nova tarefa de scraping para usuário: {usuario_atual.sub}")
        tarefa_id = str(uuid.uuid4())
        criar_tarefa(tarefa_id)

        print(f"📝 ID da tarefa: {tarefa_id}")
        print(f"📊 Total de tarefas: {len(obter_todas_tarefas())}\n")

        background_tasks.add_task(
            executar_scraper_background,
            tarefa_id,
            config
        )

        logger.info(
            "Tarefa registrada no controlador - Tarefa ID: %s", tarefa_id)
        # logger.info("Scraping iniciado em background")

        # logger.info(f"Tarefa {tarefa_id} adicionada ao background")

        return {
            "tarefa_id": tarefa_id,
            "status": "iniciado",
            "mensagem": "Scraping iniciado em background. Use o tarefa_id para monitorar progresso.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao iniciar scraping: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao iniciar scraping: {str(e)}"
        )


@router_scraping.get("/status/{tarefa_id}", summary="📥 Obter Status Detalhado da Tarefa",
                     tags=["Scraper"],
                     responses={
                         200: {
                             "description": "Status da tarefa retornado com sucesso",
                             "content": {
                                 "application/json": {
                                     "example": {
                                         "tarefa_id": "550e8400-e29b-41d4-a716-446655440000",
                                         "status": "progresso",
                                         "mensagem": "Processando página 2 de 5",
                                         "progresso": 40,
                                         "total_produtos": 24,
                                         "erro": None,
                                         "timestamp": "2025-03-12T14:31:15.654321"
                                     }
                                 }
                             }
                         },
                         404: {
                             "description": "Tarefa não encontrada",
                             "content": {
                                 "application/json": {
                                     "example": {
                                         "detail": "Tarefa com ID 'xxx-xxx' não encontrada"
                                     }
                                 }
                             }
                         },
                         500: {
                             "description": "Erro interno do servidor",
                         }
                     })
async def obter_status(tarefa_id: str):
    """Obtém status de uma tarefa"""
    try:
        logger.info(f"Busca de status solicitada para tarefa: {tarefa_id}")
        tarefa = obter_tarefa(tarefa_id)
        if not tarefa:
            logger.warning(f"Tarefa não encontrada: {tarefa_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada")

        logger.debug(f"Status da tarefa {tarefa_id}: {tarefa['status']}")

        return {
            "tarefa_id": tarefa_id,
            "status": tarefa["status"],
            "mensagem": tarefa.get("mensagem", ""),
            "progresso": tarefa.get("progresso", 0),
            "total_produtos": len(tarefa["resultados"]) if tarefa["resultados"] else 0,
            "erro": tarefa.get("erro"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(
            f"Erro ao consultar status da tarefa {tarefa_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar status: {str(e)}"
        )


@router_scraping.get("/resultados/{tarefa_id}", summary="📥 Obter Resultados da Tarefa Concluída",
                     tags=["Scraper"],
                     responses={
                         200: {
                             "description": "Resultados retornados com sucesso",
                             "content": {
                                 "application/json": {
                                     "example": {
                                         "tarefa_id": "550e8400-e29b-41d4-a716-446655440000",
                                         "total_produtos": 124,
                                         "timestamp": "2025-03-12T14:45:30.987654"
                                     }
                                 }
                             }
                         },
                         404: {
                             "description": "Tarefa não encontrada",
                         },
                         400: {
                             "description": "Tarefa ainda não foi concluída",
                             "content": {
                                 "application/json": {
                                     "example": {
                                         "detail": "Tarefa em status 'progresso'. Aguarde conclusão."
                                     }
                                 }
                             }
                         },
                         500: {
                             "description": "Erro interno do servidor",
                         }
                     })
async def obter_resultados(tarefa_id: str):
    """Obtém resultados de uma tarefa"""
    try:
        logger.info(f"Busca de resultados solicitada para tarefa: {tarefa_id}")
        tarefa = obter_tarefa(tarefa_id)

        if not tarefa:
            logger.warning(f"Tarefa não encontrada: {tarefa_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada")

        if tarefa["status"] != "concluido":
            logger.warning(
                f"Tentativa de acesso a resultados não concluídos: {tarefa_id}")
            raise HTTPException(
                status_code=400, detail=f"Tarefa em {tarefa['status']}")

        return {
            "tarefa_id": tarefa_id,
            "total_produtos": len(tarefa["resultados"]),
            "timestamp": datetime.now().isoformat()
            # "produtos": tarefa["resultados"]
        }
    except Exception as e:
        logger.error(
            f"Erro ao consultar resultados da tarefa {tarefa_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar resultados: {str(e)}"
        )


@router_scraping.get("/listar-tarefas", summary="📋 Listar Resumo de Todas as Tarefas",
                     tags=["Scraper"],
                     responses={
                         200: {
                             "description": "Lista de tarefas retornada com sucesso",
                             "content": {
                                 "application/json": {
                                     "example": {
                                         "total_tarefas": 3,
                                         "resumo": {
                                             "em_progresso": 1,
                                             "concluido": 2,
                                             "erro": 0,
                                             "aguardando": 0
                                         },
                                         "tarefas": {
                                             "550e8400-e29b-41d4-a716-446655440001": {
                                                 "tarefa_id": "550e8400-e29b-41d4-a716-446655440001",
                                                 "status": "concluido",
                                                 "progresso": 100,
                                                 "mensagem": "Scraping concluído com sucesso",
                                                 "total_produtos": 50,
                                                 "erro": None,
                                                 "timestamp_criacao": "2025-03-12T14:00:00"
                                             }
                                         },
                                         "timestamp": "2025-03-12T14:50:00"
                                     }
                                 }
                             }
                         },
                         500: {
                             "description": "Erro interno do servidor",
                         }
                     })
async def listar_tarefas():
    """Lista TODAS as tarefas"""
    try:
        print(f"\n📋 Listando tarefas...")
        logger.info("Listagem de tarefas solicitada")
        todas_tarefas = obter_todas_tarefas()

        print(f"Total: {len(todas_tarefas)}\n")

        if not todas_tarefas:
            logger.info("Nenhuma tarefa registrada")
            return {
                "total_tarefas": 0,
                "mensagem": "Nenhuma tarefa registrada",
                "resumo": {"em_progresso": 0, "concluido": 0, "erro": 0, "aguardando": 0},
                "tarefas": {},
                "timestamp": datetime.now().isoformat()
            }

        logger.debug(f"Total de tarefas encontradas: {len(todas_tarefas)}")

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

        logger.info(f"Resumo de tarefas: {contadores}")

        return {
            "total_tarefas": len(todas_tarefas),
            "resumo": contadores,
            "tarefas": tarefas_resumo,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao listar tarefas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar tarefas: {str(e)}"
        )


@router_scraping.get("/listar-tarefas-detalhado", summary="📋 Listar Tarefas com Preview de Produtos",
                     tags=["Scraper"],
                     responses={
                         200: {
                             "description": "Lista detalhada de tarefas com preview de produtos",
                             "content": {
                                 "application/json": {
                                     "example": {
                                         "total_tarefas": 2,
                                         "tarefas": [
                                             {
                                                 "tarefa_id": "550e8400-e29b-41d4-a716-446655440000",
                                                 "status": "concluido",
                                                 "total_produtos": 50,
                                                 "primeiros_5": [
                                                     {
                                                         "titulo": "The Shiing (The Shining #1) - 3 in stock",
                                                         "preco": "£49.85"
                                                     },
                                                     {
                                                         "titulo": "The Mysterious Affair at Styles",
                                                         "preco": "£46.58"
                                                     }
                                                 ]
                                             }
                                         ],
                                         "timestamp": "2025-03-12T15:00:00"
                                     }
                                 }
                             }
                         },
                         500: {
                             "description": "Erro interno do servidor",
                         }
                     })
async def listar_tarefas_detalhado():
    """Lista tarefas detalhado"""
    try:
        logger.info("Listagem detalhada de tarefas solicitada")
        todas_tarefas = obter_todas_tarefas()

        if not todas_tarefas:
            logger.info("Nenhuma tarefa registrada (listagem detalhada)")
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

        logger.debug(f"Tarefas detalhadas preparadas: {len(tarefas_lista)}")

        return {"total_tarefas": len(todas_tarefas), "tarefas": tarefas_lista, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Erro ao listar tarefas detalhadas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar tarefas detalhadas: {str(e)}"
        )


@router_scraping.get("/health",    summary="🏥 Health Check - Verificar Disponibilidade",
                     tags=["Scraper"],
                     status_code=status.HTTP_200_OK,
                     responses={
                         200: {
                             "description": "Serviço operacional",
                             "content": {
                                 "application/json": {
                                     "example": {
                                         "status": "ok",
                                         "servico": "Web Scraper API",
                                         "timestamp": "2025-03-12T15:10:00.123456"
                                     }
                                 }
                             }
                         },
                         503: {
                             "description": "Serviço indisponível",
                             "content": {
                                 "application/json": {
                                     "example": {
                                         "detail": "Problema no serviço: Banco de dados inacessível"
                                     }
                                 }
                             }
                         }
                     })
async def health_check():
    """
    Health check para verificar se a API está rodando.
    """
    try:
        logger.info("API operacional")
        return {"status": "ok", "servico": "Web Scraper API", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Health Check falhou: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Problema no serviço: {str(e)}"
        )
