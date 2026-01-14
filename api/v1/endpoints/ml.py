from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import List

from schema.ml_schema import (
    FeatureResponseSchema,
    TrainingDataResponseSchema,
    PredictionResponseSchema,
    BatchPredictionResponseSchema,
    MetricasModeloSchema,
    PredictionRequestSchema,
    BatchPredictionRequestSchema
)
from scripts.ml_service import get_ml_service
from utils.auth import verifica_token, TokenData
from utils.logger import configura_logger

logger = configura_logger(__name__, "usuarios.log")

router_ml = APIRouter()


@router_ml.get(
    "/features",
    response_model=List[FeatureResponseSchema],
    summary="Extrair Features para ML",
    description="Retorna dados formatados e normalizados para uso em modelos de ML"
)
async def get_features(
    livro_id: int = Query(
        None, description="ID específico do livro (opcional)"),
    limite: int = Query(100, ge=1, le=10000,
                        description="Limite de registros"),
    normalizar: bool = Query(True, description="Normalizar dados?"),
    current_user: TokenData = Depends(verifica_token)
):
    """
    Extrai features formatadas para modelos de ML.

    **Autenticação**: Requer JWT token válido

    **Query Parameters:**
    - `livro_id`: ID específico (opcional)
    - `limite`: Máximo 10.000 registros
    - `normalizar`: Aplicar normalização min-max

    **Resposta:**
    - `livro_id`: ID do livro
    - `features_vetor`: Array normalizado [preco, rating, categoria, disponibilidade]

    **Exemplo de uso:**
    ```python
    import requests
    response = requests.get(
        "http://api.example.com/api/v1/ml/features",
        headers={"Authorization": f"Bearer {token}"},
        params={"limite": 100, "normalizar": True}
    )
    features = response.json()
    X = [f["features_vetor"] for f in features]
    ```
    """
    try:
        logger.info(f"📊 Usuário {current_user.sub} extraindo features")

        ml_service = get_ml_service()
        features = ml_service.extrair_features(
            livro_id=livro_id,
            limite=limite,
            normalizar=normalizar
        )

        return features

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dados não disponíveis"
        )
    except Exception as e:
        logger.error(f"❌ Erro ao extrair features: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao extrair features"
        )


@router_ml.get(
    "/training-data",
    response_model=TrainingDataResponseSchema,
    summary="Dataset para Treinamento",
    description="Retorna dataset completo formatado para treinamento de modelos"
)
async def get_training_data(
    limite: int = Query(
        None, description="Limite de registros (None = todos)"),
    test_size: float = Query(
        0.2, ge=0.1, le=0.5, description="Proporção de teste"),
    current_user: TokenData = Depends(verifica_token)
):

    try:
        logger.info(f"📊 Usuário {current_user.sub} obtendo dataset de treino")

        ml_service = get_ml_service()
        dados = ml_service.obter_training_data(
            limite=limite,
            test_size=test_size
        )

        return dados

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dados não disponíveis"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Erro ao obter dados de treino: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter dados de treino"
        )


@router_ml.post(
    "/predictions",
    response_model=PredictionResponseSchema,
    summary="Fazer Predição",
    description="Faz predição para um novo livro"
)
async def fazer_predicao(
    request: PredictionRequestSchema,
    current_user: TokenData = Depends(verifica_token)
):
    """
    Faz predição de disponibilidade para um livro.

    **Autenticação**: Requer JWT token válido

    **Request:**
    ```json
    {
      "preco": 25.50,
      "rating": 4.5,
      "categoria": "Fiction"
    }
    ```

    **Resposta:**
    - `predicao`: Classe predita (0 ou 1)
    - `confianca`: Confiança da predição (0-1)
    - `classe`: Label da classe ("em_estoque" ou "fora_de_estoque")

    **Exemplo de uso:**
    ```python
    response = requests.post(
        "http://api.example.com/api/v1/ml/predictions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "preco": 25.50,
            "rating": 4.5,
            "categoria": "Fiction"
        }
    )
    pred = response.json()
    print(f"Disponibilidade predita: {pred['classe']}")
    ```
    """
    try:
        logger.info(f"🔮 Usuário {current_user.sub} fazendo predição")

        ml_service = get_ml_service()
        # ✅ PASSO 1: Se modelo não está carregado, carregar
        if ml_service.model is None:
            logger.info("📂 Carregando modelo treinado do arquivo...")
            sucesso = ml_service.carregar_modelo()

            if not sucesso:
                logger.error("❌ Falha ao carregar modelo")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Modelo não disponível. Execute o treinamento primeiro."
                )

        # ✅ PASSO 2: Fazer predição com modelo carregado
        predicao = ml_service.realizar_predicao(
            preco=request.preco,
            rating=request.rating,
            categoria=request.categoria
        )

        logger.info(f"✅ Predição realizada: {predicao['classe']}")
        return predicao

    except ValueError as e:
        logger.error(f"⚠️ Erro de validação: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise  # Re-raise HTTPException
    except Exception as e:
        logger.error(f"❌ Erro ao fazer predição: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao fazer predição"
        )


@router_ml.post(
    "/predictions/batch",
    response_model=BatchPredictionResponseSchema,
    summary="Predições em Batch",
    description="Faz múltiplas predições de uma vez"
)
async def fazer_predicoes_batch(
    request: BatchPredictionRequestSchema,
    current_user: TokenData = Depends(verifica_token)
):
    """
    Faz múltiplas predições em uma única requisição.

    **Autenticação**: Requer JWT token válido

    **Request:**
    ```json
    {
      "livros": [
        {"preco": 25.50, "rating": 4.5, "categoria": "Fiction"},
        {"preco": 35.00, "rating": 3.2, "categoria": "Science"}
      ]
    }
    ```

    **Resposta:**
    - `total_predições`: Quantidade total
    - `predições`: Array com predições
    - `tempo_total_ms`: Tempo de processamento

    **Exemplo de uso:**
    ```python
    response = requests.post(
        "http://api.example.com/api/v1/ml/predictions/batch",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "livros": [
                {"preco": 25.50, "rating": 4.5, "categoria": "Fiction"},
                {"preco": 35.00, "rating": 3.2, "categoria": "Science"}
            ]
        }
    )
    ```
    """
    try:
        logger.info(
            f"🔮 Usuário {current_user.sub} fazendo {len(request.livros)} predições em batch")

        ml_service = get_ml_service()

        if ml_service.model is None:
            logger.info("📂 Carregando modelo treinado do arquivo (batch)...")
            sucesso = ml_service.carregar_modelo()
            if not sucesso:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Modelo não disponível. Execute o treinamento primeiro."
                )

        resultado = ml_service.fazer_predicoes_batch(request.livros)

        return resultado

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar batch"
        )


@router_ml.post(
    "/train",
    response_model=MetricasModeloSchema,
    summary="Treinar Modelo",
    description="Treina novo modelo com dados atualizados utilizando RandomForestClassifier"
)
async def treinar_modelo(
    current_user: TokenData = Depends(verifica_token)
):
    """
    Treina um novo modelo com os dados atuais utilizando RandomForestClassifier.

    **Exemplo de uso:**
    ```python
    response = requests.post(
        "http://api.example.com/api/v1/ml/train",
        headers={"Authorization": f"Bearer {token_admin}"}
    )
    metricas = response.json()
    print(f"Acurácia: {metricas['acuracia']:.2%}")
    ```
    """
    try:
        from sklearn.ensemble import RandomForestClassifier

        logger.info(
            f"🤖 Admin {current_user.sub} iniciando treinamento de modelo")

        ml_service = get_ml_service()

        metricas = ml_service.treinar_modelo(
            modelo_classe=RandomForestClassifier,
            modelo_params={"n_estimators": 100, "random_state": 42}
        )

        # Salvar modelo
        ml_service.salvar_modelo(
            "models/modelo_books.pkl", "dados/scaler_books.pkl")

        logger.info(
            f"✅ Modelo treinado com acurácia {metricas['acuracia']:.2%}")

        return metricas

    except Exception as e:
        logger.error(f"❌ Erro ao treinar modelo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao treinar modelo"
        )


@router_ml.get(
    "/health",
    summary="Status do Serviço ML",
    description="Verifica se o serviço de ML está operacional"
)
async def health_check(current_user: TokenData = Depends(verifica_token)):
    """Verifica status do serviço ML"""
    try:
        ml_service = get_ml_service()

        return {
            "status": "healthy",
            "modelo_disponivel": ml_service.model is not None,
            "dados_carregados": ml_service.df is not None,
            "total_registros": len(ml_service.df) if ml_service.df is not None else 0,
            "versao_modelo": ml_service.modelo_versao
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "erro": str(e)
        }
