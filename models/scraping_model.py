from pydantic import BaseModel
from typing import Optional


# MODELOS PYDANTIC
class ConfiguracaoScraper(BaseModel):
    url_inicial: str
    section_selector: str
    li_selector: str
    next_page_selector: str
    max_paginas: Optional[int] = None
    driver_path: Optional[str] = None
    salvar_excel: bool = True


class RespostaExecucao(BaseModel):
    tarefa_id: str
    status: str
    mensagem: str
