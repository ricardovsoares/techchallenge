from pydantic import BaseModel, Field


class Book(BaseModel):
    """
    Modelo Pydantic para livros
    """
    id: int = Field(..., description="Identificador")
    titulo: str = Field(..., description="Título")
    preco: float = Field(..., description="Preço")
    rating: int = Field(..., description="Rating do Livro (1-5)")
    disponibilidade: int = Field(...,
                                 description="Marcação de Estoque")
    categoria: str = Field(..., description="Categoria do Livro")
    imagem: str = Field(..., description="URL da Capa do Livro")


class Category(BaseModel):
    """
    Modelo Pydantic para categorias de livros
    """
    name: str = Field(..., description="Categoria do Livro")


class HealthStatus(BaseModel):
    """
    Modelo Pydantic para Health Status da API
    """
    status: str = Field(..., description="Health Status da API")
    message: str = Field(..., description="Mensagem adicional")


class Statistics(BaseModel):
    """
    Nodelo Pydantic para estatísticas gerais da base de livros
    """
    total_livros: int
    total_categorias: int
    media_precos: float
    preco_minimo: float
    preco_maximo: float
    media_avaliacoes: float
    distribuicao_das_categorias: dict[str, int]
