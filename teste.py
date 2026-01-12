from models.scraping_model import ConfiguracaoScraper

# Ajuste aqui se seu build_driver estiver em outro arquivo
from utils.selenium_driver import build_driver

from utils.gerar_aquivo import salvar_em_excel, salvar_em_csv
from scripts.web_scraping_api import WebScraperComPaginacao, executar_scraper_background
from fastapi import BackgroundTasks

import uuid
from utils.estado import (
    tarefas_estado,
    tarefas_lock,
    criar_tarefa,
    obter_tarefa,
    obter_todas_tarefas,
    limpar_concluidas
)

# === EXEMPLO DE USO ===
if __name__ == "__main__":
    # Configuração - ADAPTE COM SEUS SELETORES REAIS
    URL_INICIAL = "https://books.toscrape.com/index.html"
    SECTION_SELECTOR = "section"      # ou ".produtos" ou "#products"
    # LI_SELECTOR = "li"                       # ou "li.item" ou just "li"
    LI_SELECTOR = "li.col-xs-6.col-sm-4.col-md-3.col-lg-3"
    # Botão próxima
    NEXT_PAGE_SELECTOR = "ul.pager li.next a"

    # Criar instância do scraper
    # scraper = WebScraperComPaginacao()

    config = ConfiguracaoScraper(
        url_inicial=URL_INICIAL,
        section_selector=SECTION_SELECTOR,
        li_selector=LI_SELECTOR,
        next_page_selector=NEXT_PAGE_SELECTOR,
        # max_paginas=None,
        salvar_excel=False
    )

    # scraper = WebScraperComPaginacao(
    #     driver_path=getattr(config, "driver_path", None))

    tarefa_id = str(uuid.uuid4())
    criar_tarefa(tarefa_id)

    background_tasks: BackgroundTasks = BackgroundTasks()

    craper = executar_scraper_background(tarefa_id=tarefa_id, config=config)
