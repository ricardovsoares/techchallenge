from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class FeatureResponseSchema(BaseModel):
    """Response do endpoint /features"""
    livro_id: int
    titulo: str
    preco_normalizado: float
    rating_normalizado: float
    categoria_encoded: int
    disponibilidade_encoded: int
    features_vetor: List[float]

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "livro_id": 1,
                "titulo": "O Hobbit",
                "preco_normalizado": 0.45,
                "rating_normalizado": 0.90,
                "categoria_encoded": 3,
                "disponibilidade_encoded": 1,
                "features_vetor": [0.45, 0.90, 3, 1],
            }
        }


class TrainingDataResponseSchema(BaseModel):
    """Response do endpoint /training-data (formato do MLService atual)."""
    total_registros: int = Field(..., ge=0)
    features: List[List[float]
                   ] = Field(..., description="Matriz X (preco, rating, categoria_encoded)")
    targets: List[int] = Field(...,
                               description="Vetor y (0=fora_de_estoque, 1=em_estoque)")
    feature_names: List[str] = Field(..., description="Nomes das colunas de X")
    target_name: str = Field(..., description="Nome do target")
    train_test_split: float = Field(0.8, ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "total_registros": 150,
                "features": [[25.5, 4.5, 3], [30.0, 3.8, 2]],
                "targets": [1, 0],
                "feature_names": ["preco", "rating", "categoria_encoded"],
                "target_name": "disponibilidade",
                "train_test_split": 0.8,
            }
        }


class PredictionRequestSchema(BaseModel):
    """Request usado em /predictions e /predictions/batch."""
    preco: float = Field(..., gt=0,
                         description="Preço do livro em reais", example=25.50)
    rating: float = Field(..., ge=0, le=5,
                          description="Avaliação do livro (0-5)", example=4.5)
    categoria: str = Field(..., min_length=1, max_length=100,
                           description="Categoria do livro", example="Fiction")

    class Config:
        json_schema_extra = {
            "example": {"preco": 25.50, "rating": 4.5, "categoria": "Fiction"}
        }


class PredictionResponseSchema(BaseModel):
    """Response do endpoint /predictions (alinhado ao MLService atual)."""
    livro_id: Optional[int] = Field(default=None)
    predicao: float = Field(..., description="Classe predita (0 ou 1)")
    probabilidade: float = Field(..., ge=0, le=1,
                                 description="Probabilidade da classe predita")
    confianca: float = Field(..., ge=0, le=1,
                             description="Confiança da predição (0-1)")
    classe: str = Field(...,
                        description="Label da classe (em_estoque ou fora_de_estoque)")
    modelo_versao: str
    tempo_processamento_ms: float = Field(..., ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "livro_id": None,
                "predicao": 1,
                "probabilidade": 0.95,
                "confianca": 0.95,
                "classe": "em_estoque",
                "modelo_versao": "v1.0",
                "tempo_processamento_ms": 12.5,
            }
        }


class BatchPredictionRequestSchema(BaseModel):
    """Request do endpoint /predictions/batch."""
    livros: List[PredictionRequestSchema] = Field(
        ..., min_items=1, max_items=100)
    modo_resposta: Literal["completo", "resumido"] = Field(
        default="resumido",
        description="No MLService atual o batch retorna resumido (índice/predição/confiança/classe).",
    )


class PredictionItemSchema(BaseModel):
    """Item da lista de predições (formato resumido do batch no MLService atual)."""
    livro_index: int = Field(..., ge=0,
                             description="Índice do livro na lista original")
    predicao: int = Field(..., description="Classe predita (0 ou 1)")
    confianca: float = Field(..., ge=0, le=1, description="Confiança 0-1")
    classe: str = Field(...,
                        description="Label da classe (em_estoque ou fora_de_estoque)")


class BatchPredictionResponseSchema(BaseModel):
    """Response ÚNICO do endpoint /predictions/batch (alinhado ao MLService atual)."""
    total_predicoes: int = Field(..., ge=1,
                                 description="Quantidade total de predições processadas")
    predicoes: List[PredictionItemSchema] = Field(
        ..., description="Array com predições resumidas")
    tempo_total_ms: float = Field(..., ge=0,
                                  description="Tempo total de processamento em ms")
    sucesso: bool = Field(
        default=True, description="Indica sucesso do processamento")

    class Config:
        json_schema_extra = {
            "example": {
                "total_predicoes": 2,
                "predicoes": [
                    {"livro_index": 0, "predicao": 1,
                        "confianca": 0.85, "classe": "em_estoque"},
                    {"livro_index": 1, "predicao": 0,
                        "confianca": 0.72, "classe": "fora_de_estoque"},
                ],
                "tempo_total_ms": 145.32,
                "sucesso": True,
            }
        }


class MetricasModeloSchema(BaseModel):
    """Response do endpoint /train (alinhado ao treinar_modelo do MLService ajustado)."""
    versao: str
    acuracia: float = Field(..., ge=0, le=1)
    precisao: float = Field(..., ge=0, le=1)
    recall: float = Field(..., ge=0, le=1)
    f1_score: float = Field(..., ge=0, le=1)
    data_treinamento: str = Field(...,
                                  description="ISO8601 em UTC (ex: 2026-01-13T14:16:31Z)")
    dados_usados: int = Field(..., ge=1)

    class Config:
        json_schema_extra = {
            "example": {
                "versao": "v1.0",
                "acuracia": 0.92,
                "precisao": 0.90,
                "recall": 0.89,
                "f1_score": 0.895,
                "data_treinamento": "2026-01-13T14:16:31Z",
                "dados_usados": 500,
            }
        }
