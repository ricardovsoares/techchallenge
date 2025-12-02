from fastapi import APIRouter
from api.v1.endpoints import scraping, livros

api_router = APIRouter()

api_router.include_router(scraping.router_scraping,
                          prefix='/scraper', tags=['Scraper'])

api_router.include_router(livros.router_livros,
                          prefix='/books', tags=['Books'])
