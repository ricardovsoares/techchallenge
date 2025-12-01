from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
from utils.gerar_aquivo import salvar_em_excel


class WebScraperComPaginacao:
    def __init__(self, driver_path=None):
        """
        Inicializa o WebDriver do Selenium.

        Args:
            driver_path: Caminho para o chromedriver (opcional)
        """
        if driver_path:
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service)
        else:
            self.driver = webdriver.Chrome()

        self.wait = WebDriverWait(self.driver, 10)

    def acessar_pagina(self, url):
        """
        Acessa uma URL e aguarda carregamento.

        Args:
            url: URL a ser acessada
        """
        self.driver.get(url)
        time.sleep(2)

    def extrair_linhas_da_pagina(self, section_selector, li_selector):
        """
        Extrai todas as linhas (li) dentro da section na página atual.
        Exclui elementos de paginação.

        Args:
            section_selector: Seletor CSS ou XPath da section
            li_selector: Seletor CSS ou XPath dos elementos li

        Returns:
            Lista com os hrefs encontrados na página
        """
        try:
            # Aguarda a section estar presente
            section = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, section_selector))
            )

            # Extrai todos os links (li) dentro da section
            linhas = section.find_elements(By.CSS_SELECTOR, li_selector)

            print(
                f"Elementos li encontrados (antes da filtragem): {len(linhas)}")

            hrefs = []
            for linha in linhas:
                try:
                    # Verifica se é um elemento de paginação
                    classes = linha.get_attribute("class")

                    # Pula se for parte do pager
                    if "pager" in classes or "next" in classes or "current" in classes or "prev" in classes:
                        print(f"  ⊘ Ignorado: elemento de paginação")
                        continue

                    link = linha.find_element(By.TAG_NAME, "a")
                    href = link.get_attribute("href")

                    if href:
                        hrefs.append(href)

                except Exception as e:
                    continue

            print(
                f"✓ Total de produtos extraídos (após filtragem): {len(hrefs)}\n")
            return hrefs

        except Exception as e:
            print(f"Erro ao extrair linhas: {e}")
            return []

    # Extração dos dados da página de produto
    def extrair_informacoes(self, url):
        """
        Acessa uma URL e extrai as informações desejadas.

        Args:
            url: URL da página a ser analisada

        Returns:
            Dicionário com as informações extraídas
        """
        try:
            self.driver.get(url)
            time.sleep(1)

            informacoes = {
                'url': url,
                'titulo': '',
                'descricao': '',
                'preco': '',
                'rating': '',
                'disponibilidade': '',
                'categoria': '',
                'imagem_url': ''
            }

            # Extrai o título
            try:
                titulo = self.driver.find_element(By.TAG_NAME, "h1")
                informacoes['titulo'] = titulo.text
            except:
                informacoes['titulo'] = 'Título não encontrado'

            # Extrai descrição
            try:
                secao_descricao = self.driver.find_element(
                    By.CSS_SELECTOR, 'article.product_page')
                paragrafos = secao_descricao.find_elements(By.TAG_NAME, "p")
                informacoes['descricao'] = paragrafos[3].text
            except:
                informacoes['descricao'] = 'Descrição não encontrado'

            # Extrai preço
            try:
                preco = self.driver.find_element(By.CLASS_NAME, "price_color")
                informacoes['preco'] = preco.text.replace('£', '')
            except:
                informacoes['preco'] = 'Preço não encontrado'

            # Rating
            try:
                informacoes['rating'] = self.extrair_rating(
                    url)
            except:
                informacoes['rating'] = 'Rating não encontrado'

            # Disponibilidade
            try:
                # Seleciona a classe <p instock availability>
                stock = self.driver.find_element(
                    By.CSS_SELECTOR, 'p.instock.availability')
                # XPath para o i dentro dela
                disponibilidade = stock.find_element(By.XPATH, "i")

                if disponibilidade.get_attribute('class'):
                    informacoes['disponibilidade'] = 1
                else:
                    informacoes['disponibilidade'] = 0
            except:
                informacoes['disponibilidade'] = 'Disponibilidade não encontrada'

            # Categoria
            try:
                # Encontra a categoria do produto
                breadcrumb = self.driver.find_element(
                    By.CSS_SELECTOR, 'div.page_inner ul.breadcrumb')
                # XPath para o terceiro li
                categoria = breadcrumb.find_element(By.XPATH, "li[3]")

                informacoes["categoria"] = categoria.text
            except:
                informacoes["categoria"] = 'Categoria não encontrada'

            # URL da imagem
            try:
                # Seleciona a classe <div class="item active">
                item_active = self.driver.find_element(
                    By.CSS_SELECTOR, 'div.item.active')
                # XPath para o img dentro dela
                imagem = item_active.find_element(By.XPATH, "img")

                informacoes['imagem_url'] = imagem.get_attribute('src')
            except:
                informacoes['imagem_url'] = 'Imagem não encontrada'

            return informacoes

        except Exception as e:
            print(f"Erro ao extrair informações de {url}: {e}")
            return None

    # Função auxiliar para extração da avaliação por estrelas
    def extrair_rating(self, url_detalhes):
        """
        Extrai o rating de estrelas e converte em número.
        O rating é representado por por uma classe CSS com dois nomes:
        "star-rating" e o nome do rating em inglês (ex: "Three").

        Args:
            url_detalhes: URL da página do produto

        Returns:
            Numero de estrelas (0-5)
        """

        # Dicionário de conversão
        conversao = {
            'Zero': 0,
            'One': 1,
            'Two': 2,
            'Three': 3,
            'Four': 4,
            'Five': 5
        }

        try:
            rating_element = self.driver.find_element(
                By.CSS_SELECTOR, "p.star-rating")
            classes = rating_element.get_attribute("class")

            # Pega todas as classes
            classes_lista = classes.split()

            # A segunda classe é o rating em inglês
            rating_texto = classes_lista[1]

            # Converte para número
            rating_numero = conversao.get(rating_texto, 0)

            # print(f"✓ Rating: {rating_numero} estrelas")
            return rating_numero

        except Exception as e:
            print(f"✗ Erro ao extrair rating: {e}")
        return None

    # Verifica próxima página
    def verificar_proxima_pagina(self, next_page_selector):
        """
        Verifica se existe botão/link para próxima página.

        Args:
            next_page_selector: Seletor para o link da próxima página

        Returns:
            URL da próxima página ou None se não existir
        """
        try:
            # Tenta encontrar o elemento de próxima página
            next_button = self.driver.find_element(
                By.CSS_SELECTOR,
                next_page_selector
            )

            # Extrai a URL da próxima página
            href = next_button.get_attribute("href")

            if href:
                # Converte URL relativa para absoluta se necessário
                if not href.startswith("http"):
                    base_url = self.driver.current_url.split("/catalogue/")[0]
                    href = base_url + "/catalogue/" + \
                        href.replace("catalogue/", "")

                print(f"✓ Próxima página encontrada: {href}")
                return href

            print("✗ Botão próxima página não tem href válido")
            return None

        except:
            print("✗ Não há próxima página (elemento não encontrado)")
            return None

    # Obtém página atual
    def obter_pagina_atual(self):
        """
        Extrai o número da página atual da estrutura de paginação.

        Returns:
            String com informação da página (ex: "Page 1 of 50")
        """
        try:
            pager_current = self.driver.find_element(
                By.CSS_SELECTOR,
                "ul.pager li.current"
            )
            return pager_current.text
        except:
            return "Página desconhecida"

    # Função pricipal para processar todas as páginas
    def processar_todas_paginas(
        self,
        url_inicial,
        section_selector,
        li_selector,
        next_page_selector,
        max_paginas=None
    ):
        """
        Processa todas as páginas: extrai 20 produtos por página e navega.

        Args:
            url_inicial: URL da primeira página
            section_selector: Seletor da section
            li_selector: Seletor dos elementos li
            next_page_selector: Seletor do botão/link próxima página
            max_paginas: Limite de páginas a processar (None = todas)

        Returns:
            Lista com todas as informações coletadas
        """
        url_atual = url_inicial
        pagina_numero = 1
        dados_coletados = []
        produtos_total = 0

        while url_atual and (max_paginas is None or pagina_numero <= max_paginas):
            print(f"\n{'='*70}")
            print(f"PROCESSANDO PÁGINA {pagina_numero}")
            print(f"{'='*70}")
            print(f"URL: {url_atual}")

            # Acessa a página
            self.acessar_pagina(url_atual)

            # Exibe informação de paginação
            info_paginacao = self.obter_pagina_atual()
            print(f"Status: {info_paginacao}\n")

            # Extrai os hrefs da página atual excluindo a paginação
            hrefs = self.extrair_linhas_da_pagina(
                section_selector, li_selector)

            if not hrefs:
                print("⚠ Nenhum link encontrado nesta página. Encerrando.")
                break

            # Processa cada URL da página
            for indice, href in enumerate(hrefs, 1):
                produtos_total += 1
                print(
                    f"[Pág {pagina_numero}] Produto {indice}/{len(hrefs)} (Total: {produtos_total})")
                print(f"URL: {href}")

                informacoes = self.extrair_informacoes(href)

                if informacoes:
                    dados_coletados.append(informacoes)
                    titulo_curto = informacoes['titulo'][:
                                                         50] if informacoes['titulo'] else 'Sem título'
                    print(f"✓ Sucesso | Título: {titulo_curto}")
                    if informacoes['preco']:
                        print(f"  Preço: {informacoes['preco']}")
                    if informacoes['descricao']:
                        print(f"  Descrição: {informacoes['descricao']})")
                else:
                    print(f"✗ Erro ao processar produto")

                print()  # Linha em branco para legibilidade

                # Pausa entre requisições
                time.sleep(0.5)

            # Retorna à página de listagem para navegar
            print(f"Retornando à página de listagem para próxima navegação...")
            self.acessar_pagina(url_atual)
            time.sleep(1)

            # Procura próxima página
            url_atual = self.verificar_proxima_pagina(next_page_selector)
            pagina_numero += 1

        return dados_coletados

    def fechar(self):
        """Fecha o navegador."""
        self.driver.quit()


# === USADO NOS TESTES DE CONTRUÇÃO ===
if __name__ == "__main__":
    # Configuração
    URL_INICIAL = "https://books.toscrape.com/index.html"
    SECTION_SELECTOR = "section"  # Seletor da seção onde stão a linhas dos produtos

    # Selertor LI para capturar os produtos
    LI_SELECTOR = "li.col-xs-6.col-sm-4.col-md-3.col-lg-3"

    # Seletor de próxima página
    NEXT_PAGE_SELECTOR = "ul.pager li.next a"

    # Criar instância do scraper
    scraper = WebScraperComPaginacao()

    try:
        # Processa todas as páginas
        resultados = scraper.processar_todas_paginas(
            URL_INICIAL,
            SECTION_SELECTOR,
            LI_SELECTOR,
            NEXT_PAGE_SELECTOR,
            max_paginas=None  # None = todas
        )

        # Exibe resumo dos resultados
        print(f"\n{'='*70}")
        print(f"🎉 RESUMO FINAL")
        print(f"{'='*70}")
        print(f"Total de produtos processados: {len(resultados)}")
        print(f"{'='*70}\n")

        # # Exibe os primeiros 5 produtos
        # for idx, resultado in enumerate(resultados, 1):
        #     print(f"{idx}. {resultado['titulo']}")
        #     print(f"   URL: {resultado['url']}")
        #     if resultado['preco']:
        #         print(f"   Preço: {resultado['preco']}\n")
        #         if resultado['descricao']:
        #             print(f"   Descrição: {resultado['descricao']}\n")

        if resultados:
            print("\n" + "="*70)
            print("💾 SALVANDO DADOS EM ARQUIVO...")
            print("="*70)

            # Grava os dados em Excel
            salvar_em_excel(resultados, caminho_pasta="dados",
                            nome_arquivo="catalogo_de_livros.xlsx", auto_versionar=False)

        print("\n✓ Processo concluído com sucesso.")

    except KeyboardInterrupt:
        print("\n\n⚠ Execução interrompida pelo usuário.")

    except Exception as e:
        print(f"\nErro durante execução: {e}")

    finally:
        scraper.fechar()
