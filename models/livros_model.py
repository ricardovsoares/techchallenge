from pydantic import BaseModel, Field


class Book(BaseModel):
    """
    Pydantic model for a book.
    """
    id: int = Field(..., description="Identificador")
    title: str = Field(..., description="Título")
    price: float = Field(..., description="Preço")
    rating: int = Field(..., description="Rating do Livro (1-5)")
    availability: int = Field(...,
                              description="Marcação de Estoque")
    category: str = Field(..., description="Categoria do Livro")
    image_url: str = Field(..., description="URL da Capa do Livro")


class Category(BaseModel):
    """
    Pydantic model for a book category.
    """
    name: str = Field(..., description="Categoria do Livro")


class HealthStatus(BaseModel):
    """
    Pydantic model for the API health status.
    """
    status: str = Field(..., description="Current status of the API")
    message: str = Field(..., description="Additional health message")


class Statistics(BaseModel):
    """
    Pydantic model for general book statistics.
    """
    total_books: int
    total_categories: int
    average_price: float
    min_price: float
    max_price: float
    average_rating: float
    category_distribution: dict[str, int]
