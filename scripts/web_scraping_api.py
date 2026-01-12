from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import time
import os
import socket
from typing import List, Optional, Tuple, Any, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.gerar_aquivo import salvar_em_excel, salvar_em_csv
from utils.configs import settings
from models.scraping_model import ConfiguracaoScraper, RespostaExecucao

from utils.estado import atualizar_tarefa, obter_tarefa
from utils.logger import configura_logger

# Ajuste aqui se seu build_driver estiver em outro arquivo
from utils.selenium_driver import build_driver


logger = configura_logger(__name__, "scraper_service.log")
executor = ThreadPoolExecutor(max_workers=3)


# -----------------------------
# Helpers de seletor e waits
# -----------------------------
def _is_xpath(selector: str) -> bool:
    s = (selector or "").strip()
    return s.startswith("/") or s.startswith("(") or s.startswith("./") or s.startswith(".//")


def _locator(selector: str) -> Tuple[str, str]:
    """
    Retorna (By.XPATH, selector) se parecer XPath, senão (By.CSS_SELECTOR, selector).
    """
    s = (selector or "").strip()
    if not s:
        raise ValueError("Selector vazio.")
    return (By.XPATH, s) if _is_xpath(s) else (By.CSS_SELECTOR, s)


def _safe_text(el) -> str:
    try:
        return (el.text or "").strip()
    except Exception:
        return ""


def _safe_attr(el, name: str) -> str:
    try:
        v = el.get_attribute(name)
        return (v or "").strip()
    except Exception:
        return ""


# -----------------------------
# Scraper
# -----------------------------
class WebScraperComPaginacao:
    def __init__(
        self,
        driver_path: Optional[str] = None,
        timeout: int = 15,
        headless: Optional[bool] = None,
    ):
        """
        Inicializa o WebDriver do Selenium.

        - Se driver_path for informado e existir, usa-o.
        - Caso contrário, usa build_driver() (recomendado para Docker/Render).
        """
        self.timeout = timeout

        # headless opcional (pode controlar via env SELENIUM_HEADLESS)
        # Se o build_driver já controla isso internamente, pode ignorar.
        self.headless = headless

        driver_path = (driver_path or "").strip() or None
        if driver_path and os.path.exists(driver_path):
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

            chrome_bin = os.getenv("CHROME_BIN")
            if chrome_bin and os.path.exists(chrome_bin):
                options.binary_location = chrome_bin

            service = Service(executable_path=driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("Driver iniciado via driver_path=%s", driver_path)
        else:
            self.driver = build_driver()
            logger.info("Driver iniciado via build_driver()")

        self.wait = WebDriverWait(self.driver, self.timeout)

    # ---------- Navegação ----------
    def acessar_pagina(self, url: str):
        self.driver.get(url)

        # Espera o DOM básico estar pronto (mais confiável que sleep puro)
        try:
            self.wait.until(lambda d: d.execute_script(
                "return document.readyState") in ("interactive", "complete"))
        except Exception:
            pass

        # Pequena folga para layouts dinâmicos
        time.sleep(0.5)

    # ---------- Extração de links ----------
    def extrair_hrefs_da_listagem(
        self,
        section_selector: str,
        li_selector: str,
        debug: bool = True,
    ) -> List[str]:
        """
        Tenta extrair os hrefs de produtos a partir de uma página de listagem.

        Estratégia:
        1) Encontrar a section (CSS ou XPath).
        2) Encontrar os itens (li_selector) dentro dela.
        3) Para cada item:
           - Ignorar paginação (classes pager/next/current/prev).
           - Tentar achar <a> diretamente.
           - Se não achar, tenta h3 a (muito comum em listagens de produtos).
        4) Se nada for encontrado, faz um fallback no documento inteiro:
           - procura por "article.product_pod h3 a" (BooksToScrape) e variações.
        """
        hrefs: List[str] = []

        sec_by, sec_sel = _locator(section_selector)
        li_by, li_sel = _locator(li_selector)

        # 1) encontrar section
        section = self.wait.until(
            EC.presence_of_element_located((sec_by, sec_sel)))

        # 2) esperar itens existirem (evita 0 por timing)
        def _tem_itens(_):
            try:
                return len(section.find_elements(li_by, li_sel)) > 0
            except Exception:
                return False

        try:
            self.wait.until(_tem_itens)
        except Exception:
            # segue, mas provavelmente vai dar 0
            pass

        linhas = section.find_elements(li_by, li_sel)

        if debug:
            logger.info(
                "Listagem: encontrados %s itens (antes filtragem)", len(linhas))
            if linhas:
                try:
                    logger.info("Primeiro item outerHTML (parcial): %s",
                                (linhas[0].get_attribute("outerHTML") or "")[:500])
                except Exception:
                    pass

        # 3) extrair href por item
        for idx, linha in enumerate(linhas, start=1):
            try:
                classes = _safe_attr(linha, "class")  # pode ser ""
                if any(k in classes for k in ("pager", "next", "current", "prev")):
                    continue

                # tenta <a> direto
                try:
                    a = linha.find_element(By.TAG_NAME, "a")
                    href = _safe_attr(a, "href")
                    if href:
                        hrefs.append(href)
                        continue
                except Exception:
                    pass

                # tenta <h3><a>
                try:
                    a = linha.find_element(By.CSS_SELECTOR, "h3 a")
                    href = _safe_attr(a, "href")
                    if href:
                        hrefs.append(href)
                        continue
                except Exception:
                    pass

            except Exception as e:
                if debug:
                    logger.warning(
                        "Falha ao processar item idx=%s: %r", idx, e)
                continue

        # 4) fallback global se nada foi encontrado
        if not hrefs:
            fallback_selectors = [
                "article.product_pod h3 a",
                "ol.row li article h3 a",
                "section ol li h3 a",
                "h3 a",
            ]
            for css in fallback_selectors:
                try:
                    anchors = self.driver.find_elements(By.CSS_SELECTOR, css)
                    for a in anchors:
                        href = _safe_attr(a, "href")
                        if href:
                            hrefs.append(href)
                    if hrefs:
                        if debug:
                            logger.info(
                                "Fallback funcionou com selector='%s' (hrefs=%s)", css, len(hrefs))
                        break
                except Exception:
                    continue

        # normaliza duplicados preservando ordem
        seen = set()
        unique_hrefs = []
        for h in hrefs:
            if h not in seen:
                seen.add(h)
                unique_hrefs.append(h)

        if debug:
            logger.info("Listagem: total hrefs extraídos=%s",
                        len(unique_hrefs))

        return unique_hrefs

    # ---------- Paginação ----------
    def verificar_proxima_pagina(self, next_page_selector: str) -> Optional[str]:
        """
        Retorna URL da próxima página ou None.
        Aceita CSS ou XPath.
        """
        try:
            by, sel = _locator(next_page_selector)
            next_button = self.driver.find_element(by, sel)
            href = _safe_attr(next_button, "href")
            if not href:
                return None

            # Se href for relativo e contiver "catalogue", tenta resolver como seu código original fazia
            if not href.startswith("http"):
                try:
                    base_url = self.driver.current_url.split("/catalogue/")[0]
                    href = base_url + "/catalogue/" + \
                        href.replace("catalogue/", "").lstrip("/")
                except Exception:
                    pass

            return href
        except Exception:
            return None

    def obter_pagina_atual(self) -> str:
        """
        Extrai texto do pager atual se existir.
        """
        try:
            pager_current = self.driver.find_element(
                By.CSS_SELECTOR, "ul.pager li.current")
            return _safe_text(pager_current) or "Página desconhecida"
        except Exception:
            return "Página desconhecida"

    # ---------- Extração de produto ----------
    def extrair_informacoes(self, url: str, debug: bool = False) -> Optional[Dict[str, Any]]:
        """
        Acessa uma URL e extrai as informações desejadas.
        """
        try:
            self.driver.get(url)
            try:
                self.wait.until(lambda d: d.execute_script(
                    "return document.readyState") in ("interactive", "complete"))
            except Exception:
                pass

            time.sleep(0.2)

            info = {
                "url": url,
                "titulo": "",
                "descricao": "",
                "preco": "",
                "rating": "",
                "disponibilidade": "",
                "categoria": "",
                "imagem_url": "",
            }

            # Título
            try:
                h1 = self.driver.find_element(By.TAG_NAME, "h1")
                info["titulo"] = _safe_text(h1) or "Título não encontrado"
            except Exception:
                info["titulo"] = "Título não encontrado"

            # Descrição (mais robusto que paragrafos[3])
            # Tenta BooksToScrape: #product_description + próximo <p>
            descricao = ""
            try:
                desc_title = self.driver.find_element(
                    By.CSS_SELECTOR, "#product_description")
                p = desc_title.find_element(
                    By.XPATH, "following-sibling::p[1]")
                descricao = _safe_text(p)
            except Exception:
                pass

            if not descricao:
                # fallback: tenta dentro de article.product_page, pegar o primeiro p "grande"
                try:
                    secao = self.driver.find_element(
                        By.CSS_SELECTOR, "article.product_page")
                    paragrafos = secao.find_elements(By.TAG_NAME, "p")
                    # pega o maior por texto como heurística
                    textos = [(_safe_text(p), len(_safe_text(p)))
                              for p in paragrafos]
                    textos = [t for t in textos if t[0]]
                    if textos:
                        descricao = sorted(
                            textos, key=lambda x: x[1], reverse=True)[0][0]
                except Exception:
                    pass

            info["descricao"] = descricao or "Descrição não encontrada"

            # Preço
            try:
                preco = self.driver.find_element(By.CLASS_NAME, "price_color")
                info["preco"] = _safe_text(preco).replace(
                    "£", "").strip() or "Preço não encontrado"
            except Exception:
                info["preco"] = "Preço não encontrado"

            # Rating
            try:
                # não precisa passar url
                info["rating"] = self.extrair_rating()
                if info["rating"] is None:
                    info["rating"] = "Rating não encontrado"
            except Exception:
                info["rating"] = "Rating não encontrado"

            # Disponibilidade (BooksToScrape: p.instock.availability tem texto)
            try:
                stock = self.driver.find_element(
                    By.CSS_SELECTOR, "p.instock.availability")
                stock_text = _safe_text(stock).lower()
                if "in stock" in stock_text:
                    info["disponibilidade"] = 1
                else:
                    info["disponibilidade"] = 0
            except Exception:
                info["disponibilidade"] = "Disponibilidade não encontrada"

            # Categoria (breadcrumb, li[3])
            try:
                breadcrumb = self.driver.find_element(
                    By.CSS_SELECTOR, "div.page_inner ul.breadcrumb")
                categoria = breadcrumb.find_element(By.XPATH, "li[3]")
                info["categoria"] = _safe_text(
                    categoria) or "Categoria não encontrada"
            except Exception:
                info["categoria"] = "Categoria não encontrada"

            # URL da imagem
            try:
                # BooksToScrape: div.item.active img
                img = self.driver.find_element(
                    By.CSS_SELECTOR, "div.item.active img")
                src = _safe_attr(img, "src")
                info["imagem_url"] = src or "Imagem não encontrada"
            except Exception:
                info["imagem_url"] = "Imagem não encontrada"

            if debug:
                logger.info("Produto extraído: titulo=%s preco=%s",
                            info.get("titulo"), info.get("preco"))

            return info

        except Exception as e:
            if debug:
                logger.exception(
                    "Erro ao extrair informações de %s: %r", url, e)
            return None

    def extrair_rating(self) -> Optional[int]:
        """
        Extrai rating de estrelas do BooksToScrape (p.star-rating + classe One/Two/...).
        """
        conversao = {"Zero": 0, "One": 1, "Two": 2,
                     "Three": 3, "Four": 4, "Five": 5}

        try:
            rating_element = self.driver.find_element(
                By.CSS_SELECTOR, "p.star-rating")
            classes = _safe_attr(rating_element, "class")
            if not classes:
                return None

            parts = classes.split()
            if len(parts) < 2:
                return None

            rating_texto = parts[1]
            return conversao.get(rating_texto, 0)
        except Exception:
            return None

    def fechar(self):
        try:
            if getattr(self, "driver", None):
                self.driver.quit()
        except Exception:
            pass

    # ---------- Fluxo principal ----------
    def processar_todas_paginas(
        self,
        url_inicial: str,
        section_selector: str,
        li_selector: str,
        next_page_selector: str,
        max_paginas: Optional[int] = None,
        controller=None,
        debug: bool = True,
    ) -> List[Dict[str, Any]]:
        url_atual = url_inicial
        pagina_numero = 1
        dados_coletados: List[Dict[str, Any]] = []
        produtos_total = 0

        while url_atual and (max_paginas is None or pagina_numero <= max_paginas):

            if controller and hasattr(controller, "is_stop_requested") and controller.is_stop_requested():
                logger.warning("Parada solicitada durante processamento")
                break

            if debug:
                print(f"\n{'='*70}")
                print(f"PROCESSANDO PÁGINA {pagina_numero}")
                print(f"{'='*70}")
                print(f"URL: {url_atual}")

            self.acessar_pagina(url_atual)

            if debug:
                print("TITLE:", self.driver.title)
                print("CURRENT_URL:", self.driver.current_url)
                print(f"{'-'*70}")

            info_paginacao = self.obter_pagina_atual()
            if debug:
                print(f"Status: {info_paginacao}\n")

            hrefs = self.extrair_hrefs_da_listagem(
                section_selector=section_selector,
                li_selector=li_selector,
                debug=debug,
            )

            if not hrefs:
                if debug:
                    print("⚠ Nenhum link encontrado nesta página. Encerrando.")
                break

            for indice, href in enumerate(hrefs, 1):
                produtos_total += 1
                if debug:
                    print(
                        f"[Pág {pagina_numero}] Produto {indice}/{len(hrefs)} (Total: {produtos_total})")
                    print(f"URL: {href}")

                info = self.extrair_informacoes(href, debug=False)
                if info:
                    dados_coletados.append(info)
                    if debug:
                        titulo_curto = (info.get("titulo") or "")[
                            :50] or "Sem título"
                        print(f"✓ Sucesso | Título: {titulo_curto}")
                        if info.get("preco"):
                            print(f"  Preço: {info.get('preco')}")
                        if info.get("descricao"):
                            print(
                                f"  Descrição: {(info.get('descricao') or '')[:120]}...")
                else:
                    if debug:
                        print("✗ Erro ao processar produto")

                if debug:
                    print()

                time.sleep(0.2)

            # Próxima página
            url_atual = self.verificar_proxima_pagina(next_page_selector)
            pagina_numero += 1

        return dados_coletados


# -----------------------------
# Execução em background
# -----------------------------
def executar_scraper_background(tarefa_id: str, config: ConfiguracaoScraper):
    """
    Executa o scraper em thread separada.
    """
    scraper = None

    try:
        atualizar_tarefa(
            tarefa_id,
            status="em_progresso",
            mensagem="Iniciando scraper...",
            progresso=5,
        )

        logger.info(
            "Scraper start tarefa_id=%s hostname=%s driver_path=%r CHROME_BIN=%r CHROMEDRIVER=%r",
            tarefa_id,
            socket.gethostname(),
            getattr(config, "driver_path", None),
            os.getenv("CHROME_BIN"),
            os.getenv("CHROMEDRIVER"),
        )

        print(f"\n{'='*70}")
        print(f"🚀 EXECUTANDO TAREFA {tarefa_id}")
        print(f"{'='*70}\n")

        scraper = WebScraperComPaginacao(
            driver_path=getattr(config, "driver_path", None))

        resultados = scraper.processar_todas_paginas(
            url_inicial=config.url_inicial,
            section_selector=config.section_selector,
            li_selector=config.li_selector,
            next_page_selector=config.next_page_selector,
            max_paginas=config.max_paginas,
            controller=getattr(config, "controller", None),
            debug=True,
        )

        # Salvar arquivos
        if resultados:
            if getattr(config, "salvar_excel", False):
                salvar_em_excel(
                    resultados,
                    caminho_pasta=settings.DIR_BASE,
                    nome_arquivo=settings.BASE,
                    auto_versionar=False,
                )
            else:
                salvar_em_csv(
                    resultados,
                    caminho_pasta=settings.DIR_BASE,
                    nome_arquivo=settings.BASE,
                    auto_versionar=False,
                )

        atualizar_tarefa(
            tarefa_id,
            status="concluido",
            progresso=100,
            mensagem=f"✓ Scraping concluído! {len(resultados)} produtos coletados.",
            resultados=resultados,
            erro=None,
            timestamp_conclusao=datetime.now().isoformat(),
        )

        print(f"\n{'='*70}")
        print(f"✅ TAREFA {tarefa_id} CONCLUÍDA")
        print(f"📦 Total de produtos: {len(resultados)}")
        print(f"{'='*70}\n")

    except Exception as e:
        logger.exception("Erro na tarefa %s: %r", tarefa_id, e)

        print(f"\n{'='*70}")
        print(f"❌ ERRO NA TAREFA {tarefa_id}")
        print(f"Erro: {str(e)}")
        print(f"{'='*70}\n")

        atualizar_tarefa(
            tarefa_id,
            status="erro",
            progresso=0,
            mensagem=f"Erro: {str(e)}",
            resultados=None,
            erro=str(e),
            timestamp_conclusao=datetime.now().isoformat(),
        )

    finally:
        try:
            if scraper:
                scraper.fechar()
        except Exception:
            pass
