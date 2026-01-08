from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

# ============= ENUMS =============


class DisponibilidadeEnum(str, Enum):
    """Estados de disponibilidade"""
    em_estoque = "em_estoque"
    fora_de_estoque = "fora_de_estoque"
    pre_venda = "pre_venda"

# ============= SCHEMAS DE REQUEST =============


class FeatureRequestSchema(BaseModel):
    """Request para extrair features"""
    livro_id: Optional[int] = None
    limite: int = Field(default=100, ge=1, le=10000)
    normalizar: bool = Field(default=True, description="Normalizar dados?")

    class Config:
        description = "Parametros para extrair features formatadas para ML"


class PredictionRequestSchema(BaseModel):
    """Request para fazer predição"""
    preco: float = Field(..., gt=0, description="Preço do livro")
    rating: float = Field(..., ge=0, le=5, description="Rating (0-5)")
    categoria: str = Field(..., min_length=1, description="Categoria do livro")

    class Config:
        example = {
            "preco": 25.50,
            "rating": 4,
            "categoria": "Fiction"
        }


class BatchPredictionRequestSchema(BaseModel):
    """Request para múltiplas predições"""
    livros: List[PredictionRequestSchema] = Field(
        ..., min_items=1, max_items=1000)
    modelo_versao: str = Field(
        default="latest", description="Versão do modelo")

    class Config:
        example = {
            "livros": [
                {"preco": 25.50, "rating": 4.5, "categoria": "Fiction"},
                {"preco": 35.00, "rating": 3.2, "categoria": "Science"}
            ],
            "modelo_versao": "latest"
        }
