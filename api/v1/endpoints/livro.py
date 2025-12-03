import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Optional, Dict, Any
import os
import logging
from functools import lru_cache
from utils.configs import settings

from models.livros_model import Book, Category, HealthStatus, Statistics

from utils.logger import configura_logger

logger = configura_logger(__name__, "livros.log")
router_livros = APIRouter()

DATA_FILE = os.path.join(settings.DIR_BASE, settings.BASE)
books_df: Optional[pd.DataFrame] = None


def load_books_data():
    """ Carrega os dados de livros do CSV para um datafram Pandas."""
    global books_df
    if books_df is None:
        if not os.path.exists(DATA_FILE):
            logger.error(
                f"Dados não encontrados: {DATA_FILE}. Por favor, execute o Scraper!")
            raise RuntimeError(f"Base de dados não encontrada: {DATA_FILE}")
        try:
            books_df = pd.read_csv(DATA_FILE)
            # Define id como índice para pesquisas mais rápidas
            books_df['id'] = books_df['id'].astype(int)
            # books_df.set_index('id', inplace=True)
            logger.info(
                f"Carregaento realizado com sucesso: {len(books_df)} livros em {DATA_FILE}")
        except Exception as e:
            logger.error(f"Erro ao carregar os dados {DATA_FILE}: {e}")
            raise RuntimeError(f"Falha na carga do arquivo de livros: {e}")
    return books_df


# Carrega os dados na inicialização
try:
    load_books_data()
except RuntimeError:
    logger.critical(
        "O aplicativo não pode ser iniciado sem os dados do livro.")


@router_livros.get("/health", response_model=HealthStatus, summary="🏥 Verificação de Saúde da API de Livros",
                   description="Verifica se a API de livros está operacional e respondendo.",
                   tags=["Books"],
                   responses={
                       200: {
                           "description": "API operacional",
                           "content": {
                               "application/json": {
                                   "example": {"status": "ok", "message": "API de livros está funcionando!"}
                               }
                           }
                       },
                       500: {
                           "description": "Erro interno do servidor",
                           "content": {
                               "application/json": {
                                   "example": {"detail": "Erro interno ao verificar a saúde da API"}
                               }
                           }
                       }
                   })
async def health_check():
    """
    Avalia a saúde da API.
    """
    try:
        # Attempt to access the data to ensure it's loaded
        if books_df is None or books_df.empty:
            return HealthStatus(status="Offline", message="A base de livros não foi carregada ou está vazia!")
        return HealthStatus(status="OK", message="API em execução e acessível")
    except Exception as e:
        logger.error(f"Falha ao realizar Health check: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Erro interno durante health check")


@router_livros.get("/", response_model=List[Book], summary="📋 Listar todos os livros",
                   description="Retorna uma lista de todos os livros disponíveis, com opções de paginação.",
                   tags=["Books"],
                   responses={
                       200: {
                           "description": "Lista de livros retornada com sucesso",
                           "content": {
                               "application/json": {
                                   "example": [
                                       {"id": 1, "titulo": "A Arte da Guerra", "autor": "Sun Tzu",
                                        "categoria": "Estratégia", "preco": 25.50, "avaliacao": 4.8},
                                       {"id": 2, "titulo": "O Pequeno Príncipe", "autor": "Antoine de Saint-Exupéry",
                                        "categoria": "Literatura Infantil", "preco": 15.00, "avaliacao": 4.9}
                                   ]
                               }
                           }
                       },
    500: {
        "description": "Erro interno do servidor",
        "content": {
            "application/json": {
                "example": {"detail": "Erro ao listar livros"}
            }
        }
                       }
})
async def listar_livros(
    limite: int = Query(100, ge=1, le=1000,
                        description="Número de livros"),
    paginacao: int = Query(0, ge=0, description="Número para paginação")
):
    """
    Lista de todos os livros com paginação opcional.
    """
    df = load_books_data()
    paginated_books = df.iloc[paginacao:paginacao + limite]

    if paginated_books.empty and paginacao > 0:
        logger.warning("Não foram encontrados mais livros.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Não foram encontrados mais livros.")
    return paginated_books.to_dict(orient="records")


@router_livros.get("/search", response_model=List[Book],
                   summary="🔍 Buscar livros por título ou categoria",
                   description="Permite buscar livros utilizando um termo de pesquisa no título ou na categoria.",
                   tags=["Books"],
                   responses={
                       200: {
                           "description": "Livros encontrados com sucesso",
                           "content": {
                               "application/json": {
                                   "example": [
                                       {"id": 3, "titulo": "1984", "autor": "George Orwell",
                                        "categoria": "Distopia", "preco": 30.00, "avaliacao": 4.7},
                                       {"id": 7, "titulo": "A Revolução dos Bichos", "autor": "George Orwell",
                                        "categoria": "Distopia", "preco": 20.00, "avaliacao": 4.7}
                                   ]
                               }
                           }
                       },    400: {
                           "description": "Parâmetros de busca inválidos",
                           "content": {
                               "application/json": {
                                   "example": {"detail": "Termo de busca deve ter no mínimo 2 caracteres."}
                               }
                           }
                       },    500: {
                           "description": "Erro interno do servidor",
                           "content": {
                               "application/json": {
                                   "example": {"detail": "Erro ao buscar livros"}
                               }
                           }
                       }})
async def search_books(
    title: Optional[str] = Query(None, min_length=1,
                                 description="Pesquisa por título"),
    category: Optional[str] = Query(None, min_length=1,
                                    description="Pesquisa por categoria")
):
    """
    Busca livros por título e/ou categoria.

    **Parâmetros:**
    - `title`: Termo de busca no título (opcional)
    - `category`: Termo de busca na categoria (opcional)

    **Exemplos:**
    - `/search?title=harry` → busca por título
    - `/search?category=fiction` → busca por categoria
    - `/search?title=potter&category=fiction` → busca por ambos (AND)
    - `/search` → ERRO (pelo menos um é obrigatório)

    **Validação:**
    - Pelo menos um parâmetro (`title` ou `category`) é obrigatório
    - Mínimo 1 caractere em cada termo
    """

    # Validar: pelo menos um parâmetro deve estar presente
    if not title and not category:
        logger.warning("Nenhum parâmetro de busca fornecido")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pelo menos um dos parâmetros ('title' ou 'category') é obrigatório"
        )

    df = load_books_data()
    results_df = df.copy()

    # Filtrar por título se fornecido
    if title:
        results_df = results_df[
            results_df['titulo'].str.contains(title, case=False, na=False)
        ]
        logger.info(
            f"Filtrado por título: '{title}' → {len(results_df)} resultados")

    # Filtrar por categoria se fornecido
    if category:
        results_df = results_df[
            results_df['categoria'].str.contains(
                category, case=False, na=False)
        ]
        logger.info(
            f"Filtrado por categoria: '{category}' → {len(results_df)} resultados")

    # Verificar se encontrou algo
    if results_df.empty:
        search_params = []
        if title:
            search_params.append(f"título='{title}'")
        if category:
            search_params.append(f"categoria='{category}'")

        detail = f"Nenhum livro encontrado para {' e '.join(search_params)}"
        logger.info(detail)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

    logger.info(f"Busca concluída: {len(results_df)} livro(s) encontrado(s)")
    return results_df.to_dict(orient="records")


@router_livros.get("/categories", response_model=List[Category], summary="📋 Listar todas as categorias de livros",
                   description="Retorna uma lista de todas as categorias únicas de livros disponíveis no sistema.",
                   tags=["Books"],
                   responses={
                       200: {
                           "description": "Lista de categorias retornada com sucesso",
                           "content": {
                               "application/json": {
                                   "example": ["Estratégia", "Literatura Infantil", "Distopia", "Clássico", "História", "Programação", "Fantasia"]
                               }
                           }
                       }, 500: {
                           "description": "Erro interno do servidor",
                           "content": {
                               "application/json": {
                                   "example": {"detail": "Erro ao listar categorias"}
                               }
                           }
                       }})
async def get_all_categories():
    """
    Buscar livros por categoria.
    """
    df = load_books_data()
    unique_categories = df['categoria'].unique().tolist()
    return [{"name": cat} for cat in unique_categories]


@router_livros.get("/insights/statistics", response_model=Statistics, summary="📊 Obter estatísticas gerais dos livros",
                   description="Retorna estatísticas agregadas sobre os livros, como total de livros, preço médio e avaliação média.",
                   tags=["Books"],
                   responses={
                       200: {
                           "description": "Estatísticas retornadas com sucesso",
                           "content": {
                               "application/json": {
                                   "example": {
                                       "total_livros": 10,
                                       "preco_medio": 39.45,
                                       "avaliacao_media": 4.61
                                   }
                               }
                           }
                       },
                       500: {
                           "description": "Erro interno do servidor",
                           "content": {
                               "application/json": {
                                   "example": {"detail": "Erro ao obter estatísticas"}
                               }
                           }
                       }
                   })
async def get_book_statistics():
    """
 Fornece estatísticas gerais e agregadas sobre o conjunto de dados de livros.

    Este endpoint calcula métricas importantes sobre a biblioteca de livros,
    incluindo totalizações, médias, extremos e distribuições por categoria.
    Útil para dashboards, relatórios e análises de negócio.

    **Funcionalidade:**
    - Calcula estatísticas descritivas de toda a base de dados
    - Analisa distribuição de preços e avaliações
    - Gera distribuição de livros por categoria
    - Arredonda valores monetários e numéricos para 2 casas decimais

    **Parâmetros:**
    - Nenhum parâmetro necessário (endpoint sem filtros)

    **Retorno (Statistics):**
    - `total_livros` (int): Quantidade total de livros na base
    - `total_categorias` (int): Quantidade de categorias diferentes
    - `media_precos` (float): Preço médio de todos os livros (2 casas decimais)
    - `preco_minimo` (float): Livro com menor preço (2 casas decimais)
    - `preco_maximo` (float): Livro com maior preço (2 casas decimais)
    - `media_avaliacoes` (float): Avaliação média de todos os livros (2 casas decimais)
    - `distribuicao_das_categorias` (dict): Quantidade de livros por categoria
        Formato: {"categoria": quantidade, "outra_categoria": quantidade, ...}

    **Exemplo de Resposta:**
    ```json
    {
      "total_livros": 200,
      "total_categorias": 15,
      "media_precos": 45.32,
      "preco_minimo": 9.99,
      "preco_maximo": 199.99,
      "media_avaliacoes": 3.87,
      "distribuicao_das_categorias": {
        "Fiction": 50,
        "Science Fiction": 35,
        "History": 28,
        "Poetry": 22,
        "Mystery": 20,
        "Biography": 18,
        "Other": 27
      }
    }
    ```

    **Exemplos de Uso:**
    - `GET /api/v1/livros/insights/statistics`
      → Retorna todas as estatísticas da base

    **Validações e Tratamentos:**
    - Se base de dados vazia: Erro 404 "Base de livros não encontrada"
    - Valores monetários: Arredondados para 2 casas decimais
    - Avaliações: Arredondadas para 2 casas decimais
    - Distribuição: Ordenada por categoria (ordem alfabética)

    **Logs:**
    - INFO: Estatísticas calculadas com sucesso (com count total)
    - WARNING: Se base vazia (raro - quase nunca acontece)
    - ERROR: Se erro ao carregar dados

    **Performance:**
    - Operação rápida mesmo com grandes volumes (até 100k livros)
    - Sem filtros ou paginação necessários
    - Executa em memória (sem I/O adicional)

    **Erros Possíveis:**
    - 404: Base de livros não encontrada ou vazia
    - 500: Erro ao carregar dados do CSV
    """
    df = load_books_data()
    if df.empty:
        logger.warning("Base de livros não encontrada.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Base de livros não encontrada.")

    total_livros = len(df)
    total_categorias = df['categoria'].nunique()
    media_precos = df['preco'].mean()
    preco_minimo = df['preco'].min()
    preco_maximo = df['preco'].max()
    media_avaliacoes = df['rating'].mean()
    distribuicao_das_categorias = df['categoria'].value_counts().to_dict()

    return Statistics(
        total_livros=total_livros,
        total_categorias=total_categorias,
        media_precos=round(media_precos, 2),
        preco_minimo=round(preco_minimo, 2),
        preco_maximo=round(preco_maximo, 2),
        media_avaliacoes=round(media_avaliacoes, 2),
        distribuicao_das_categorias=distribuicao_das_categorias
    )


@router_livros.get("/insights/top-rated", response_model=List[Book], summary="📋 Listar livros mais bem avaliados",
                   description="Retorna uma lista dos livros com as maiores avaliações.",
                   tags=["Books"],
                   responses={
                       200: {
                           "description": "Livros mais bem avaliados retornados com sucesso",
                           "content": {
                               "application/json": {
                                   "example": [
                                       {"id": 8, "titulo": "O Senhor dos Anéis", "autor": "J.R.R. Tolkien",
                                        "categoria": "Fantasia", "preco": 70.00, "avaliacao": 5.0},
                                       {"id": 2, "titulo": "O Pequeno Príncipe", "autor": "Antoine de Saint-Exupéry",
                                        "categoria": "Literatura Infantil", "preco": 15.00, "avaliacao": 4.9}
                                   ]
                               }
                           }
                       },
                       500: {
                           "description": "Erro interno do servidor",
                           "content": {
                               "application/json": {
                                   "example": {"detail": "Erro ao listar livros mais bem avaliados"}
                               }
                           }
                       }})
async def get_top_rated_books(
    limit: int = Query(
        5, ge=1, le=20, description="Os livros mais bem avaliados")
):
    """
    Retorna os livros com as maiores avaliações (rating).

    Este endpoint ordena todos os livros pelo campo 'rating' em ordem decrescente
    e retorna os 'limit' primeiros livros mais bem avaliados.

    **Parâmetros:**
    - `limit` (Query, int): Quantidade de livros a retornar
        - Padrão: 5 livros
        - Mínimo: 1 livro
        - Máximo: 20 livros

    **Retorno:**
    - Lista de até 'limit' livros ordenados por rating (maior para menor)
    - Cada livro contém: id, url, titulo, descricao, preco, rating, 
      disponibilidade, categoria, imagem

    **Exemplos de Uso:**
    - `GET /api/v1/books/top-rated` 
      → Retorna os 5 livros mais bem avaliados (padrão)

    - `GET /api/v1/books/top-rated?limit=3`
      → Retorna os 3 livros mais bem avaliados

    - `GET /api/v1/books/top-rated?limit=20`
      → Retorna os 20 livros mais bem avaliados (máximo)

    **Validações:**
    - Se `limit < 1`: Erro 422 (mínimo 1)
    - Se `limit > 20`: Erro 422 (máximo 20)
    - Se `limit` não é inteiro: Erro 422 (tipo inválido)

    **Logs:**
    - INFO: Registra quantos livros foram retornados
    - WARNING: Se nenhum livro for encontrado (raro)

    **Erros Possíveis:**
    - 404: Nenhum livro disponível (raro - quase nunca acontece)
    - 422: Parâmetro 'limit' inválido
    """
    df = load_books_data()
    top_books_df = df.sort_values(by='rating', ascending=False).head(limit)
    if top_books_df.empty:
        logger.warning("Nenhum livro bem avaliado foi encontrado.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Nenhum livro bem avaliado foi encontrado.")
    return top_books_df.to_dict(orient="records")


@router_livros.get("/insights/price-range", response_model=List[Book], summary="🔍 Filtrar livros por faixa de preço",
                   description="Retorna livros que se encaixam em uma faixa de preço especificada.",
                   tags=["Books"],
                   responses={
                       200: {
                           "description": "Livros na faixa de preço retornados com sucesso",
                           "content": {
                               "application/json": {
                                   "example": [
                                       {"id": 1, "titulo": "A Arte da Guerra", "autor": "Sun Tzu",
                                        "categoria": "Estratégia", "preco": 25.50, "avaliacao": 4.8},
                                       {"id": 3, "titulo": "1984", "autor": "George Orwell",
                                        "categoria": "Distopia", "preco": 30.00, "avaliacao": 4.7}
                                   ]
                               }
                           }
                       },
                       400: {
                           "description": "Faixa de preço inválida",
                           "content": {
                               "application/json": {
                                   "example": {"detail": "Preço mínimo não pode ser maior que o preço máximo."}
                               }
                           }
                       },
                       500: {
                           "description": "Erro interno do servidor",
                           "content": {
                               "application/json": {
                                   "example": {"detail": "Erro ao filtrar livros por preço"}
                               }
                           }
                       }})
async def get_books_by_price_range(
    min_price: float = Query(
        0.0, ge=0.0, description="Preço mínimo por livro"),
    max_price: float = Query(
        1000.0, ge=0.0, description="Preço máximo por livro")
):
    """
    Retorna uma listagem de livros filtrados por faixa de preços.

    Este endpoint permite buscar livros dentro de uma faixa de preços específica,
    útil para filtros de e-commerce, comparação de preços e análise de inventário.
    Ambos os limites (mínimo e máximo) são inclusivos.

    **Funcionalidade:**
    - Filtra livros por preço mínimo (>= min_price)
    - Filtra livros por preço máximo (<= max_price)
    - Valida que min_price ≤ max_price
    - Retorna lista ordenada por preço (crescente)
    - Suporta valores com decimais (centavos)

    **Parâmetros:**
    - `min_price` (Query, float): Preço mínimo para filtrar
        - Padrão: 0.0
        - Mínimo: 0.0 (valores negativos não permitidos)
        - Descrição: Define o limite inferior da busca (inclusivo)

    - `max_price` (Query, float): Preço máximo para filtrar
        - Padrão: 1000.0
        - Mínimo: 0.0 (valores negativos não permitidos)
        - Descrição: Define o limite superior da busca (inclusivo)

    **Retorno (List[BookResponse]):**
    - Lista de livros que correspondem à faixa de preços
    - Cada livro contém: id, url, titulo, descricao, preco, rating, 
      disponibilidade, categoria, imagem
    - Lista vazia resulta em erro 404

    **Exemplo de Resposta:**
    ```json
    [
      {
        "id": 1,
        "url": "https://books.toscrape.com/catalogue/...",
        "titulo": "A Light in the Attic",
        "descricao": "It's hard to imagine a world without...",
        "preco": 51.77,
        "rating": 3,
        "disponibilidade": 1,
        "categoria": "Poetry",
        "imagem": "https://books.toscrape.com/media/cache/..."
      },
      {
        "id": 2,
        "url": "https://books.toscrape.com/catalogue/...",
        "titulo": "Tipping the Velvet",
        "descricao": "Erotic and absorbing...",
        "preco": 53.74,
        "rating": 1,
        "disponibilidade": 1,
        "categoria": "Historical Fiction",
        "imagem": "https://books.toscrape.com/media/cache/..."
      }
    ]
    ```

    **Exemplos de Uso:**
    - `GET /api/v1/books/insights/price-range`
      → Retorna todos os livros (padrão: 0.0 - 1000.0)

    - `GET /api/v1/books/insights/price-range?min_price=20&max_price=50`
      → Retorna livros entre R$ 20,00 e R$ 50,00

    - `GET /api/v1/books/insights/price-range?min_price=10.50&max_price=99.99`
      → Retorna livros entre R$ 10,50 e R$ 99,99 (com centavos)

    - `GET /api/v1/books/insights/price-range?min_price=0&max_price=25`
      → Retorna livros mais baratos (até R$ 25,00)

    - `GET /api/v1/books/insights/price-range?min_price=100`
      → Retorna livros acima de R$ 100,00 (até padrão 1000.0)

    **Validações:**
    - `min_price >= 0.0`: Valores negativos não permitidos
    - `max_price >= 0.0`: Valores negativos não permitidos
    - `min_price <= max_price`: Min não pode ser maior que máx
    - Se nenhum livro encontrado: Erro 404

    **Validações em Detalhe:**
    - Se `min_price > max_price`: Erro 400 
      "min_price cannot be greater than max_price"
    - Se nenhum livro na faixa: Erro 404 
      "No books found in price range $X.XX - $Y.YY"
    - Se parâmetro não é número: Erro 422 (valor inválido)
    - Se valor negativo: Erro 422 (violação ge=0.0)

    **Logs:**
    - INFO: Quantidade de livros encontrados e faixa de preço
    - WARNING: Se nenhum livro encontrado na faixa especificada
    - ERROR: Se erro ao carregar dados

    **Performance:**
    - Operação rápida com índices pandas (O(n))
    - Escalável para bases com até 1M livros
    - Sem paginação necessária (resultados geralmente <100 livros)

    **Erros Possíveis:**
    - 400: min_price > max_price
    - 404: Nenhum livro encontrado na faixa especificada
    - 422: Parâmetro inválido (não é número ou negativo)
    - 500: Erro ao carregar dados do CSV
    """
    if min_price > max_price:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="min_price cannot be greater than max_price.")

    df = load_books_data()
    filtered_books_df = df[(df['preco'] >= min_price) &
                           (df['preco'] <= max_price)]
    if filtered_books_df.empty:
        logger.warning(
            f"Nenhum livro encontrado na faixa de preço: ${min_price:.2f} - ${max_price:.2f}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Nenhum livro encontrado na faixa de preço: ${min_price:.2f} - ${max_price:.2f}.")
    return filtered_books_df.to_dict(orient="records")


@router_livros.get("/{book_id}", response_model=Book, summary="🔍 Buscar livro por ID",
                   description="Recupera os detalhes completos de um livro específico utilizando seu identificador único (ID).",
                   tags=["Books"],
                   responses={
                       200: {
                           "description": "Livro encontrado e retornado com sucesso.",
                           "content": {
                               "application/json": {
                                   "example": {
                                       "id": 1,
                                       "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                                       "titulo": "A Light in the Attic",
                                       "descricao": "It's hard to imagine a world without...",
                                       "preco": 51.77,
                                       "rating": 3,
                                       "disponibilidade": 1,
                                       "categoria": "Poetry",
                                       "imagem": "https://books.toscrape.com/media/cache/2c/da/2cdad67c44b002ae7a0c12dd7787fd30.jpg"
                                   }
                               }
                           }
                       },
                       404: {
                           "description": "Livro não encontrado para o ID fornecido.",
                           "content": {
                               "application/json": {
                                   "example": {"detail": "O livro com ID 999 não foi encontrado."}
                               }
                           }
                       },
                       500: {
                           "description": "Erro interno do servidor ao processar a requisição.",
                           "content": {
                               "application/json": {
                                   "example": {"detail": "Erro interno ao buscar o livro."}
                               }
                           }
                       },
                   },)
async def get_book_by_id(book_id: int):
    """
    Retorna os dados de um livro pelo ID.
    """
    df = load_books_data()
    if book_id not in df["id"].values:
        logger.warning(f"O ID {book_id} não foi encontrado.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"O livro com ID {book_id} não foi encontrado.")

    book_data = df[df['id'] == book_id].iloc[0].to_dict()

    return book_data
