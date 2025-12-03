from fastapi import APIRouter
from api.v1.endpoints import livro, scraping, usuario

api_router = APIRouter()

api_router.include_router(scraping.router_scraping,
                          prefix='/scraper', tags=['Scraper'])

api_router.include_router(livro.router_livros,
                          prefix='/books', tags=['Books'])

api_router.include_router(
    usuario.router_usuario, prefix='/users', tags=['Users'])
