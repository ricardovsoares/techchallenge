from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class FeatureResponseSchema(BaseModel):
    """Response com features formatadas"""
    livro_id: int
    titulo: str
    preco_normalizado: float
    rating_normalizado: float
    categoria_encoded: int
    disponibilidade_encoded: int
    features_vetor: List[float]

    class Config:
        from_attributes = True
        example = {
            "livro_id": 1,
            "titulo": "O Hobbit",
            "preco_normalizado": 0.45,
            "rating_normalizado": 0.90,
            "categoria_encoded": 3,
            "disponibilidade_encoded": 1,
            "features_vetor": [0.45, 0.90, 3, 1]
        }


class PredictionItemSchema(BaseModel):
    livro_index: int = Field(
        ...,
        ge=0,
        description="Índice do livro na lista original"
    )
    predicao: int = Field(
        ...,
        description="Classe predita (0 ou 1)"
    )
    confianca: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confiança 0-1"
    )
    classe: str = Field(
        ...,
        description="Label da classe (em_estoque ou fora_de_estoque)"
    )

# ✅ Schema da resposta completa


class BatchPredictionResponseSchema(BaseModel):
    total_predicoes: int = Field(
        ...,
        ge=1,
        description="Quantidade total"
    )
    predicoes: List[PredictionItemSchema] = Field(
        ...,
        description="Array com todas as predições"
    )
    tempo_total_ms: float = Field(
        ...,
        ge=0,
        description="Tempo de processamento em ms"
    )
    sucesso: bool = Field(
        default=True,
        description="Indica sucesso do processamento"
    )


class TrainingDataResponseSchema(BaseModel):
    """Response com dataset para treinamento"""
    total_registros: int
    features: List[List[float]]
    targets: List[int]
    feature_names: List[str]
    target_name: str
    train_test_split: float = 0.8

    class Config:
        example = {
            "total_registros": 150,
            "features": [[0.45, 0.90, 3, 1], [0.55, 0.80, 2, 1]],
            "targets": [1, 0],
            "feature_names": ["preco_norm", "rating_norm", "categoria", "disponivel"],
            "target_name": "disponibilidade",
            "train_test_split": 0.8
        }


class PredictionResponseSchema(BaseModel):
    """Response com predição"""
    livro_id: Optional[int] = None
    predicao: float
    probabilidade: float
    confianca: float = Field(..., ge=0, le=1,
                             description="Confiança da predição (0-1)")
    classe: str = Field(..., description="Classe predita")
    modelo_versao: str
    tempo_processamento_ms: float

    class Config:
        example = {
            "livro_id": None,
            "predicao": 1,
            "probabilidade": 0.95,
            "confianca": 0.95,
            "classe": "disponível",
            "modelo_versao": "v1.0",
            "tempo_processamento_ms": 12.5
        }


class BatchPredictionResponseSchema(BaseModel):
    """Response com múltiplas predições"""
    total_predições: int
    predições: List[PredictionResponseSchema]
    tempo_total_ms: float
    modelo_versao: str


class MetricasModeloSchema(BaseModel):
    """Métricas do modelo treinado"""
    versao: str
    acuracia: float
    precisao: float
    recall: float
    f1_score: float
    data_treinamento: str
    dados_usados: int

    class Config:
        example = {
            "versao": "v1.0",
            "acuracia": 0.92,
            "precisao": 0.90,
            "recall": 0.89,
            "f1_score": 0.895,
            "data_treinamento": "2024-01-15T10:30:00Z",
            "dados_usados": 500
        }


class PredictionRequestSchema(BaseModel):
    preco: float = Field(
        ...,                          # Campo obrigatório
        gt=0,                         # Greater than 0
        description="Preço do livro em reais",
        example=25.50
    )
    rating: float = Field(
        ...,
        ge=0,                         # Greater or equal 0
        le=5,                         # Less or equal 5
        description="Avaliação do livro (0-5 estrelas)",
        example=4.5
    )
    categoria: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Categoria do livro",
        example="Fiction"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "preco": 25.50,
                "rating": 4.5,
                "categoria": "Fiction"
            }
        }


class BatchPredictionRequestSchema(BaseModel):
    livros: List[PredictionRequestSchema] = Field(
        ..., min_items=1, max_items=100)
    modo_resposta: Literal["completo", "resumido"] = Field(
        default="completo",
        description="Retorna detalhes completos ou apenas predição"
    )


class BatchPredictionResponseSchema(BaseModel):
    """
    Schema para resposta de múltiplas predições em batch.

    Contém todas as predições processadas, estatísticas
    e informações de performance.
    """
    total_predicoes: int = Field(
        ...,
        ge=1,
        description="Quantidade total de predições processadas",
        example=2
    )
    predicoes: List[PredictionItemSchema] = Field(
        ...,
        description="Array com todas as predições individuais",
        example=[
            {
                "livro_index": 0,
                "predicao": 1,
                "confianca": 0.85,
                "classe": "em_estoque"
            },
            {
                "livro_index": 1,
                "predicao": 0,
                "confianca": 0.72,
                "classe": "fora_de_estoque"
            }
        ]
    )
    tempo_total_ms: float = Field(
        ...,
        ge=0,
        description="Tempo total de processamento em milissegundos",
        example=145.32
    )
    sucesso: bool = Field(
        default=True,
        description="Indica se todas as predições foram bem-sucedidas",
        example=True
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_predicoes": 2,
                "predicoes": [
                    {
                        "livro_index": 0,
                        "predicao": 1,
                        "confianca": 0.85,
                        "classe": "em_estoque"
                    },
                    {
                        "livro_index": 1,
                        "predicao": 0,
                        "confianca": 0.72,
                        "classe": "fora_de_estoque"
                    }
                ],
                "tempo_total_ms": 145.32,
                "sucesso": True
            }
        }
