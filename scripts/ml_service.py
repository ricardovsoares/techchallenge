import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from utils.configs import settings

logger = logging.getLogger(__name__)


class MLService:
    """Serviço para operações de ML (consistente com endpoints FastAPI)."""

    def __init__(self, csv_path: str = None):
        self.csv_path = csv_path or (settings.DIR_BASE + "/" + settings.BASE)
        self.df: Optional[pd.DataFrame] = None
        self.scaler: StandardScaler = StandardScaler()
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.modelo_versao = "v1.0"
        self.model = None
        self.modelo_path = Path("dados/modelo_books.pkl")
        self.scaler_path = Path("dados/scaler_books.pkl")
        self.allow_default_fallback = True
        self._carregar_dados()
        self._inicializar_encoders()

    def _minmax(self, v: float, s: pd.Series) -> float:
        mn, mx = float(s.min()), float(s.max())
        return 0.0 if mx == mn else (float(v) - mn) / (mx - mn)

    def _normalizar_disponibilidade(self, v: Any, strict: bool = True) -> str:
        s = str(v).strip().lower()
        em = {"1", "true", "sim", "yes", "em_estoque", "em estoque",
              "in stock", "available", "disponivel", "disponível"}
        fora = {"0", "false", "nao", "não", "no", "fora_de_estoque", "fora de estoque",
                "out of stock", "unavailable", "indisponivel", "indisponível"}
        if s in em:
            return "em_estoque"
        if s in fora:
            return "fora_de_estoque"
        if not strict:
            return s
        raise ValueError(f"Valor de disponibilidade não reconhecido: {v}")

    def _carregar_dados(self) -> None:
        if not os.path.exists(self.csv_path):
            logger.error(f"❌ CSV não encontrado: {self.csv_path}")
            raise FileNotFoundError(f"CSV não encontrado: {self.csv_path}")

        df = pd.read_csv(self.csv_path)
        esperadas = {"id", "titulo", "preco",
                     "rating", "disponibilidade", "categoria"}
        if not esperadas.issubset(df.columns):
            raise ValueError(f"Colunas faltando. Esperadas: {esperadas}")

        df["preco"] = pd.to_numeric(df["preco"], errors="coerce")
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
        df = df.dropna(subset=["preco", "rating",
                       "disponibilidade", "categoria"])
        df["disponibilidade"] = df["disponibilidade"].apply(
            lambda x: self._normalizar_disponibilidade(x, strict=False))
        self.df = df
        logger.info(
            f"✅ {len(self.df)} registros carregados de {self.csv_path}")

    def _inicializar_encoders(self) -> None:
        cats = list(self.df["categoria"].astype(str).unique())
        if "Default" not in cats:
            cats.append("Default")

        le_cat = LabelEncoder()
        le_cat.fit(cats)

        le_disp = LabelEncoder()
        le_disp.fit(["fora_de_estoque", "em_estoque"])  # 0=fora, 1=em

        self.label_encoders = {"categoria": le_cat, "disponibilidade": le_disp}

    def _encode_categoria(self, categoria: Any) -> int:
        cat = str(categoria)
        le = self.label_encoders["categoria"]
        if cat in le.classes_:
            return int(le.transform([cat])[0])
        if self.allow_default_fallback:
            return int(le.transform(["Default"])[0])
        raise ValueError(f"Categoria inválida: {categoria}")

    def _inicializar_encoders(self) -> None:
        cats = list(self.df["categoria"].astype(str).unique())
        if "Default" not in cats:
            cats.append("Default")

        le_cat = LabelEncoder()
        le_cat.fit(cats)

        le_disp = LabelEncoder()
        le_disp.fit(["fora_de_estoque", "em_estoque"])  # 0=fora, 1=em

        self.label_encoders = {"categoria": le_cat, "disponibilidade": le_disp}

    def _encode_categoria(self, categoria: Any) -> int:
        cat = str(categoria)
        le = self.label_encoders["categoria"]
        if cat in le.classes_:
            return int(le.transform([cat])[0])
        if self.allow_default_fallback:
            return int(le.transform(["Default"])[0])
        raise ValueError(f"Categoria inválida: {categoria}")

    def _feature_dict(self, row: pd.Series, normalizar: bool) -> Dict[str, Any]:
        preco = float(row["preco"])
        rating = float(row["rating"])
        preco_n = self._minmax(
            preco, self.df["preco"]) if normalizar else preco
        rating_n = self._minmax(
            rating, self.df["rating"]) if normalizar else rating
        cat_e = self._encode_categoria(row["categoria"])
        disp = self._normalizar_disponibilidade(
            row["disponibilidade"], strict=False)
        if disp not in ("em_estoque", "fora_de_estoque"):
            disp = "fora_de_estoque"
        disp_e = int(
            self.label_encoders["disponibilidade"].transform([disp])[0])
        fv = [float(preco_n), float(rating_n), float(cat_e), float(disp_e)]
        return {"livro_id": int(row["id"]),
                "titulo": str(row["titulo"]),
                "preco_normalizado": float(preco_n),
                "rating_normalizado": float(rating_n),
                "categoria_encoded": int(cat_e),
                "disponibilidade_encoded": int(disp_e),
                "features_vetor": fv}

    def extrair_features(self, livro_id: Optional[int] = None, limite: int = 100, normalizar: bool = True) -> List[Dict[str, Any]]:
        dados = self.df[self.df["id"] == livro_id] if livro_id else self.df
        dados = dados.head(limite)
        if dados.empty:
            return []
        return [self._feature_dict(row, normalizar) for _, row in dados.iterrows()]

    def obter_training_data(self, limite: Optional[int] = None, test_size: float = 0.2) -> Dict[str, Any]:
        dados = self.df.head(limite) if limite else self.df
        if dados.empty:
            raise ValueError("Nenhum dado disponível para treinamento")

        disp_norm = dados["disponibilidade"].apply(
            lambda v: self._normalizar_disponibilidade(v, strict=True))
        y = np.array(
            [1 if d == "em_estoque" else 0 for d in disp_norm.tolist()], dtype=int)
        cat = dados["categoria"].apply(
            self._encode_categoria).to_numpy(dtype=int)
        X = np.column_stack([dados["preco"].astype(
            float).to_numpy(), dados["rating"].astype(float).to_numpy(), cat])

        strat = y if np.unique(y).size > 1 else None
        Xtr, Xte, ytr, yte = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=strat)

        le_cat = self.label_encoders["categoria"]
        le_disp = self.label_encoders["disponibilidade"]
        return {"total_registros": int(len(dados)),
                "features": X.tolist(),
                "targets": y.tolist(),
                "features_train": Xtr.tolist(),
                "targets_train": ytr.tolist(),
                "features_test": Xte.tolist(),
                "targets_test": yte.tolist(),
                "feature_names": ["preco", "rating", "categoria_encoded"], "target_name": "disponibilidade", "train_test_split": float(1 - test_size),
                "categorias_mapping": {int(i): str(c) for i, c in enumerate(le_cat.classes_)},
                "disponibilidade_mapping": {int(i): str(c) for i, c in enumerate(le_disp.classes_)}}

    def treinar_modelo(self, modelo_classe, modelo_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from datetime import datetime, timezone
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

        modelo_params = modelo_params or {}

        data = self.obter_training_data(limite=None, test_size=0.2)
        X = np.array(data["features"], dtype=float)
        y = np.array(data["targets"], dtype=int)

        stratify = y if np.unique(y).size >= 2 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )

        self.scaler = StandardScaler()
        X_train_s = self.scaler.fit_transform(X_train)
        X_test_s = self.scaler.transform(X_test)

        self.model = modelo_classe(**modelo_params)
        self.model.fit(X_train_s, y_train)

        y_pred = self.model.predict(X_test_s)

        metricas = {
            "versao": str(self.modelo_versao),
            "acuracia": float(accuracy_score(y_test, y_pred)),
            "precisao": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
            "data_treinamento": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "dados_usados": int(len(X)),
        }

        # ✅ Salva automaticamente nos paths padrão configurados no __init__
        self.salvar_modelo(str(self.modelo_path), str(self.scaler_path))

        return metricas

    def salvar_modelo(self, modelo_path: str, scaler_path: str) -> None:
        if self.model is None or self.scaler is None:
            raise ValueError("Modelo e/ou scaler não disponíveis para salvar.")

        self.modelo_path = Path(modelo_path)
        self.scaler_path = Path(scaler_path)
        self.modelo_path.parent.mkdir(parents=True, exist_ok=True)
        self.scaler_path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.model, self.modelo_path)
        joblib.dump(self.scaler, self.scaler_path)

    def carregar_modelo(self) -> bool:
        try:
            if not self.modelo_path.exists() or not self.scaler_path.exists():
                return False
            self.model = joblib.load(self.modelo_path)
            self.scaler = joblib.load(self.scaler_path)
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            return False

    def _preparar_features(self, preco: float, rating: float, categoria: str) -> np.ndarray:
        if not isinstance(preco, (int, float)) or preco < 0:
            raise ValueError(f"Preço inválido: {preco}")
        if not isinstance(rating, (int, float)) or not (0 <= rating <= 5):
            raise ValueError(f"Rating inválido: {rating}")
        cat_e = self._encode_categoria(categoria)
        return np.array([[float(preco), float(rating), float(cat_e)]], dtype=float)

    def _validar_entrada(self, preco: Any, rating: Any) -> None:
        if not isinstance(preco, (int, float)) or float(preco) < 0:
            raise ValueError(f"❌ Preço inválido: {preco}")

        if not isinstance(rating, (int, float)) or not (0 <= float(rating) <= 5):
            raise ValueError(f"❌ Rating inválido: {rating}")

    def realizar_predicao(self, preco: float, rating: float, categoria: str) -> Dict[str, Any]:
        if self.model is None:
            raise ValueError(
                "Modelo não carregado. Execute /train ou carregar_modelo().")

        t0 = time.time()

        self._validar_entrada(preco, rating)

        cat_enc = self._encode_categoria(categoria)
        X = np.array(
            [[float(preco), float(rating), float(cat_enc)]], dtype=float)
        Xs = self.scaler.transform(X)

        pred_int = int(self.model.predict(Xs)[0])
        classe = "em_estoque" if pred_int == 1 else "fora_de_estoque"

        prob = 1.0
        if hasattr(self.model, "predict_proba"):
            probas = self.model.predict_proba(Xs)[0]
            classes = list(getattr(self.model, "classes_", [0, 1]))
            if pred_int in classes:
                prob = float(probas[classes.index(pred_int)])
            else:
                prob = float(np.max(probas))

        tempo_ms = float((time.time() - t0) * 1000.0)

        return {
            "livro_id": None,
            "predicao": float(pred_int),
            "probabilidade": float(prob),
            "confianca": float(prob),
            "classe": classe,
            "modelo_versao": str(self.modelo_versao),
            "tempo_processamento_ms": tempo_ms,
        }

    def fazer_predicoes_batch(self, livros: List[Any]) -> Dict[str, Any]:
        if self.model is None:
            raise ValueError(
                "Modelo não carregado. Execute /train ou carregar_modelo().")
        t0 = time.time()
        predicoes = []
        for idx, l in enumerate(livros):
            preco = l.preco if hasattr(l, "preco") else l.get("preco")
            rating = l.rating if hasattr(l, "rating") else l.get("rating")
            categoria = l.categoria if hasattr(
                l, "categoria") else l.get("categoria")
            r = self.realizar_predicao(
                float(preco), float(rating), str(categoria))
            predicoes.append({"livro_index": idx, "predicao": int(
                r["predicao"]), "confianca": float(r["confianca"]), "classe": r["classe"]})
        return {"total_predicoes": len(predicoes), "predicoes": predicoes, "tempo_total_ms": (time.time()-t0)*1000, "sucesso": True}


ml_service: Optional[MLService] = None


def get_ml_service() -> MLService:
    global ml_service
    if ml_service is None:
        ml_service = MLService()
    return ml_service
