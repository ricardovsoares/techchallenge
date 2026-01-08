import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import logging
from datetime import datetime
import time
from typing import Dict, List, Any, Optional
import os
from utils.configs_bkp import settings
from pathlib import Path
import json
import pickle

logger = logging.getLogger(__name__)


class MLService:
    """Serviço para operações de ML"""

    def __init__(self, csv_path: str = settings.DIR_BASE + "/" + settings.BASE):
        self.csv_path = csv_path
        self.df = None
        self.scaler = StandardScaler()
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.modelo_versao = "v1.0"
        self.modelo = None
        self.model = None
        self._carregar_dados()
        self._inicializar_encoders()
        self.modelo_path = Path("models/modelo_treinado.pkl")
        self.scaler_path = Path("models/scaler.pkl")
        self.categoria_map = {}  # Dicionário vazio inicialmente
        self.categoria_map_path = Path("models")
        self.categoria_map = {
            "Poetry": 0,
            "Historical Fiction": 1,
            "Fiction": 2,
            "Mystery": 3,
            "History": 4,
            "Young Adult": 5,
            "Business": 6,
            "Default": 7,
            "Sequential Art": 8,
            "Music": 9,
            "Science Fiction": 10,
            "Politics": 11,
            "Travel": 12
        }

    def _carregar_dados(self) -> None:
        """Carrega dados do CSV"""
        try:
            if not os.path.exists(self.csv_path):
                logger.error(f"❌ Arquivo {self.csv_path} não encontrado")
                raise FileNotFoundError(f"CSV não encontrado: {self.csv_path}")

            self.df = pd.read_csv(self.csv_path)
            logger.info(
                f"✅ {len(self.df)} registros carregados de {self.csv_path}")

            # Validar colunas
            colunas_esperadas = {"id", "titulo", "preco",
                                 "rating", "disponibilidade", "categoria"}
            if not colunas_esperadas.issubset(self.df.columns):
                raise ValueError(
                    f"Colunas faltando. Esperadas: {colunas_esperadas}")

            # Limpar dados
            self.df["preco"] = pd.to_numeric(self.df["preco"], errors="coerce")
            self.df["rating"] = pd.to_numeric(
                self.df["rating"], errors="coerce")
            self.df = self.df.dropna(
                subset=["preco", "rating", "disponibilidade"])

            logger.info(f"✅ Dados limpos. {len(self.df)} registros válidos")

        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados: {e}")
            raise

    def _inicializar_encoders(self) -> None:
        """Inicializa label encoders para variáveis categóricas"""
        try:
            # Encoder para categoria
            self.label_encoders["categoria"] = LabelEncoder()
            self.label_encoders["categoria"].fit(self.df["categoria"].unique())

            # Encoder para disponibilidade (target)
            self.label_encoders["disponibilidade"] = LabelEncoder()
            self.label_encoders["disponibilidade"].fit(
                self.df["disponibilidade"].unique())

            logger.info("✅ Encoders inicializados")

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar encoders: {e}")
            raise

    def carregar_modelo(self):
        """Carrega modelo e scaler do arquivo"""
        try:
            # Verificar se arquivo existe
            if not self.modelo_path.exists():
                logger.warning(
                    f"📁 Caminho esperado: {self.modelo_path.absolute()}")
                raise FileNotFoundError(
                    f"Modelo não encontrado em {self.modelo_path}"
                )

            # Carregar modelo
            logger.info(f"📂 Carregando modelo de {self.modelo_path}...")
            self.model = joblib.load(self.modelo_path)

            # Carregar scaler (normalização)
            if self.scaler_path.exists():
                logger.info(f"📂 Carregando scaler de {self.scaler_path}...")
                self.scaler = joblib.load(self.scaler_path)

            logger.info("✅ Modelo carregado com sucesso!")
            return True

        except FileNotFoundError as e:
            logger.error(f"❌ {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            return False

    def _normalizar_preco(self, preco: float) -> float:
        """Normaliza preço (0-1)"""
        min_preco = self.df["preco"].min()
        max_preco = self.df["preco"].max()
        return (preco - min_preco) / (max_preco - min_preco)

    def _normalizar_rating(self, rating: float) -> float:
        """Normaliza rating (0-1)"""
        return rating / 5.0  # Rating é 0-5

    def extrair_features(
        self,
        livro_id: Optional[int] = None,
        limite: int = 100,
        normalizar: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extrai features formatadas para ML.

        Args:
            livro_id: ID específico (opcional)
            limite: Quantidade máxima de registros
            normalizar: Se deve normalizar os dados

        Returns:
            Lista de features formatadas
        """
        try:
            logger.info(
                f"📊 Extraindo features (limite={limite}, normalizar={normalizar})")

            # Filtrar dados
            if livro_id:
                dados = self.df[self.df["id"] == livro_id].head(limite)
            else:
                dados = self.df.head(limite)

            if dados.empty:
                logger.warning(f"⚠️ Nenhum dado encontrado")
                return []

            features_list = []

            for row in dados.iterrows():
                # Normalizar preço e rating
                preco_norm = self._normalizar_preco(
                    row["preco"]) if normalizar else row["preco"]
                rating_norm = self._normalizar_rating(
                    row["rating"]) if normalizar else row["rating"]

                # Encode categoria
                categoria_encoded = int(
                    self.label_encoders["categoria"].transform([row["categoria"]])[0])

                # Disponibilidade (1 = disponível, 0 = não disponível)
                disponibilidade_encoded = int(
                    self.label_encoders["disponibilidade"].transform(
                        [row["disponibilidade"]])[0]
                )

                # Montar vetor de features
                features_vetor = [
                    float(preco_norm),
                    float(rating_norm),
                    float(categoria_encoded),
                    float(disponibilidade_encoded)
                ]

                feature_dict = {
                    "livro_id": int(row["id"]),
                    "titulo": str(row["titulo"]),
                    "preco_normalizado": float(preco_norm),
                    "rating_normalizado": float(rating_norm),
                    "categoria_encoded": categoria_encoded,
                    "disponibilidade_encoded": disponibilidade_encoded,
                    "features_vetor": features_vetor
                }

                features_list.append(feature_dict)

            logger.info(f"✅ {len(features_list)} features extraídas")
            return features_list

        except Exception as e:
            logger.error(f"❌ Erro ao extrair features: {e}")
            raise

    def obter_training_data(
        self,
        limite: Optional[int] = None,
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Retorna dataset formatado para treinamento.

        Args:
            limite: Quantidade máxima de registros
            test_size: Proporção para teste (0.2 = 80/20)

        Returns:
            Dict com features, targets e metadados
        """
        try:
            logger.info(
                f"📊 Preparando dados para treinamento (test_size={test_size})")

            # Usar limite se especificado
            dados = self.df.head(limite) if limite else self.df

            if dados.empty:
                raise ValueError("Nenhum dado disponível para treinamento")

            # Features
            X = []
            y = []

            for idx, row in dados.iterrows():
                # Features normalizadas
                preco_norm = self._normalizar_preco(row["preco"])
                rating_norm = self._normalizar_rating(row["rating"])
                categoria_encoded = int(
                    self.label_encoders["categoria"].transform([row["categoria"]])[0])

                features = [preco_norm, rating_norm, categoria_encoded]
                X.append(features)

                # Target: disponibilidade
                target = int(self.label_encoders["disponibilidade"].transform(
                    [row["disponibilidade"]])[0])
                y.append(target)

            # Converter para numpy
            X = np.array(X)
            y = np.array(y)

            # Dividir treino/teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

            resultado = {
                "total_registros": len(dados),
                "features": X.tolist(),
                "targets": y.tolist(),
                "features_train": X_train.tolist(),
                "targets_train": y_train.tolist(),
                "features_test": X_test.tolist(),
                "targets_test": y_test.tolist(),
                "feature_names": ["preco_normalizado", "rating_normalizado", "categoria_encoded"],
                "target_name": "disponibilidade",
                "train_test_split": 1 - test_size,
                "categorias_mapping": {
                    int(i): cat for i, cat in enumerate(
                        self.label_encoders["categoria"].classes_
                    )
                },
                "disponibilidade_mapping": {
                    int(i): disp for i, disp in enumerate(
                        self.label_encoders["disponibilidade"].classes_
                    )
                }
            }

            logger.info(
                f"✅ Dataset preparado: {len(X_train)} train, {len(X_test)} test")
            return resultado

        except Exception as e:
            logger.error(f"❌ Erro ao preparar dados: {e}")
            raise

    def _encontrar_arquivo(self, caminho: str) -> Optional[str]:
        """
        Procura pelo arquivo em múltiplos locais

        Args:
            caminho: Caminho original do arquivo

        Returns:
            str: Caminho válido se encontrado, None caso contrário
        """
        caminho = str(caminho)
        # 1️⃣ Verificar caminho exato
        if Path(caminho).exists():
            logger.debug(f"✅ Arquivo encontrado no caminho exato: {caminho}")
            return caminho

        # 2️⃣ Verificar caminho relativo a partir do diretório atual
        caminho_relativo = Path.cwd() / caminho
        if caminho_relativo.exists():
            logger.debug(
                f"✅ Arquivo encontrado em diretório relativo: {caminho_relativo}")
            return str(caminho_relativo)

        # 3️⃣ Verificar apenas o nome do arquivo em diretórios comuns
        nome_arquivo = Path(caminho).name
        diretorios_busca = [
            Path.cwd(),
            Path.cwd() / "models",
            Path.cwd() / "data",
            Path.home() / "models",
        ]

        for diretorio in diretorios_busca:
            caminho_candidato = diretorio / nome_arquivo
            if caminho_candidato.exists():
                logger.debug(f"✅ Arquivo encontrado em: {caminho_candidato}")
                return str(caminho_candidato)

        # 4️⃣ Listar o que foi procurado
        logger.error(f"❌ Arquivo não encontrado: {caminho}")
        logger.error(f"📂 Diretório atual: {Path.cwd()}")
        logger.error(
            f"📁 Arquivos procurados em: {[str(d) for d in diretorios_busca]}")

        # Listar arquivos .pkl disponíveis
        arquivos_pkl = list(Path.cwd().glob("**/*.pkl"))
        if arquivos_pkl:
            logger.error(f"📦 Arquivos .pkl encontrados no sistema:")
            for pkl in arquivos_pkl[:5]:  # Mostra até 5
                logger.error(f"   - {pkl}")
        else:
            logger.error(f"❌ Nenhum arquivo .pkl encontrado no diretório!")

        return None

    def _carregar_arquivos(self):
        """Carrega o scaler e o modelo dos arquivos .pkl"""
        try:
            # Carregar scaler
            if self.scaler_path:
                caminho_scaler = self._encontrar_arquivo(self.scaler_path)
                if caminho_scaler:
                    with open(caminho_scaler, 'rb') as arquivo_scaler:
                        self.scaler = pickle.load(arquivo_scaler)
                    logger.info(f"✅ Scaler carregado com sucesso")
                else:
                    logger.warning(
                        f"⚠️ Scaler não encontrado. Prosseguindo sem normalização")

            # Carregar modelo
            caminho_modelo = self._encontrar_arquivo(self.modelo_path)
            if caminho_modelo:
                with open(caminho_modelo, 'rb') as arquivo_modelo:
                    self.modelo = pickle.load(arquivo_modelo)
                logger.info(f"✅ Modelo carregado com sucesso")
            else:
                raise FileNotFoundError(
                    f"Modelo não encontrado em: {self.modelo_path}\n"
                    f"Verifique se o arquivo existe no diretório correto"
                )

        except pickle.UnpicklingError as e:
            logger.error(f"❌ Erro ao desserializar arquivo: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao carregar arquivos: {e}")
            raise

    def _preparar_features(self, preco: float, rating: float, categoria: str) -> List[float]:
        """
        Converte entrada em features numéricas com validação e encoding

        Args:
            preco: Preço do livro (float)
            rating: Avaliação do livro (float, 0-5)
            categoria: Categoria do livro (str)

        Returns:
            list: Array com 3 features numéricas

        Raises:
            ValueError: Se valores estão fora do intervalo esperado
        """
        # ✅ VALIDAÇÃO 1: Preço válido?
        if not isinstance(preco, (int, float)) or preco < 0:
            raise ValueError(
                f"❌ Preço inválido: {preco}. Deve ser número positivo")

        # ✅ VALIDAÇÃO 2: Rating válido?
        if not isinstance(rating, (int, float)) or not (0 <= rating <= 5):
            raise ValueError(
                f"❌ Rating inválido: {rating}. Deve estar entre 0 e 5")

        # ✅ VALIDAÇÃO 3: Categoria existe no mapa?
        if categoria not in self.categoria_map:
            categorias_validas = list(self.categoria_map.keys())
            raise ValueError(
                f"❌ Categoria '{categoria}' inválida. "
                f"Categorias válidas: {categorias_validas}")

        # ✅ ENCODE: Transformar categoria em número usando LabelEncoder
        categoria_encoded = self.label_encoders["categoria"].transform([categoria])[
            0]

        logger.debug(
            f"📊 Features preparadas: preco={preco}, rating={rating}, "
            f"categoria='{categoria}' (encoded={categoria_encoded})")

        return [preco, rating, categoria_encoded]

    def realizar_predicao(self, preco: float, rating: float, categoria: str) -> Dict[str, Any]:
        """
        Realiza predição com o modelo carregado

        Args:
            preco: Preço do livro em reais (float)
            rating: Avaliação do livro de 0 a 5 (float)
            categoria: Categoria do livro (str)

        Returns:
            dict: Dicionário contendo:
                - predicao: Valor numérico da predição (0 ou 1)
                - confianca: Confiança da predição (0-1)
                - classe: Classe predita (em_estoque ou fora_de_estoque)
                - detalhes: Detalhes adicionais da predição

        Raises:
            ValueError: Se modelo não está carregado ou parametros inválidos

        Example:
            >>> preditor = PreditorLivros(...)
            >>> resultado = preditor.realizar_predicao(29.90, 4.5, "ficção")
            >>> print(resultado["classe"])
            'em_estoque'
        """
        self._carregar_arquivos()

        # ✅ VALIDAÇÃO: Modelo carregado?
        if self.modelo is None:
            raise ValueError(
                "❌ Modelo não carregado. Verifique o arquivo modelo.pkl")

        try:
            # Preparar features com validação e encoding
            features = self._preparar_features(preco, rating, categoria)

            # Aplicar normalização se disponível
            if self.scaler is not None:
                features_normalizadas = self.scaler.transform([features])
                logger.debug("✅ Features normalizadas com scaler")
            else:
                logger.warning(
                    "⚠️ Scaler não disponível. Usando features sem normalização")
                features_normalizadas = [features]

            # Fazer predição
            predicao_numerica = self.modelo.predict(features_normalizadas)[0]
            confianca = float(self.modelo.predict_proba(
                features_normalizadas)[0].max())

            # Obter probabilidades para ambas as classes
            probabilidades = self.modelo.predict_proba(
                features_normalizadas)[0]

            # Mapear para classe legível
            classe = "em_estoque" if predicao_numerica == 1 else "fora_de_estoque"

            logger.info(
                f"📈 Predição realizada com sucesso: "
                f"classe={classe}, confiança={confianca:.2%}")

            return {
                "predicao": int(predicao_numerica),
                "confianca": round(confianca, 4),
                "classe": classe,
                "detalhes": {
                    "preco": preco,
                    "rating": rating,
                    "categoria": categoria,
                    "probabilidade_fora_estoque": round(float(probabilidades[0]), 4),
                    "probabilidade_em_estoque": round(float(probabilidades[1]), 4)
                }
            }

        except ValueError as e:
            logger.error(f"❌ Erro de validação: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao realizar predição: {e}")
            raise


ml_service = None


def get_ml_service() -> MLService:
    """Retorna instância do serviço (singleton)"""
    global ml_service
    if ml_service is None:
        ml_service = MLService()
    return ml_service
