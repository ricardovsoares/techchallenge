from typing import Optional, Dict

from pydantic import BaseModel, Field


class Book(BaseModel):
    """Schema de livro (response_model dos endpoints que retornam livros)."""
    id: int
    url: Optional[str] = None
    titulo: str
    descricao: Optional[str] = None
    preco: float = Field(ge=0, description="Preço do livro")
    rating: float = Field(ge=0, le=5, description="Avaliação do livro (0-5)")
    disponibilidade: int = Field(
        ge=0, le=1, description="Disponibilidade (0=fora_de_estoque, 1=em_estoque)")
    categoria: str
    imagem: Optional[str] = None

    # Pode existir em exemplos/datasets alternativos, então mantemos opcional
    autor: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                "titulo": "A Light in the Attic",
                "descricao": "It's hard to imagine a world without...",
                "preco": 51.77,
                "rating": 3,
                "disponibilidade": 1,
                "categoria": "Poetry",
                "imagem": "https://books.toscrape.com/media/cache/2c/da/2cdad67c44b002ae7a0c12dd7787fd30.jpg",
                "autor": None
            }
        }


class Category(BaseModel):
    """Schema para o endpoint /categories."""
    name: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {"name": "Fiction"}
        }


class HealthStatus(BaseModel):
    """Schema para o endpoint /health."""
    status: str = Field(..., description="Status do serviço (ex: OK, Offline)")
    message: str = Field(..., description="Mensagem descritiva do status")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {"status": "OK", "message": "API em execução e acessível"}
        }


class Statistics(BaseModel):
    """Schema para o endpoint /insights/statistics."""
    total_livros: int = Field(..., ge=0)
    total_categorias: int = Field(..., ge=0)
    media_precos: float = Field(..., ge=0)
    preco_minimo: float = Field(..., ge=0)
    preco_maximo: float = Field(..., ge=0)
    media_avaliacoes: float = Field(..., ge=0, le=5)
    distribuicao_das_categorias: Dict[str, int] = Field(
        ...,
        description="Quantidade de livros por categoria. Ex: {'Fiction': 50, 'Poetry': 20}"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "total_livros": 200,
                "total_categorias": 15,
                "media_precos": 45.32,
                "preco_minimo": 9.99,
                "preco_maximo": 199.99,
                "media_avaliacoes": 3.87,
                "distribuicao_das_categorias": {
                    "Fiction": 50,
                    "Science Fiction": 35,
                    "History": 28
                }
            }
        }
