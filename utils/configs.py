from typing import ClassVar, List, Optional
import os
import json
import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator
from sqlalchemy.orm import declarative_base


class Settings(BaseSettings):
    """
    Configurações gerais da aplicação.

    - Em development/local: carrega .env
    - Em production no Render: lê apenas variáveis de ambiente (Config Vars)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """
        Controla as fontes do Pydantic Settings (v2).

        - Produção (Render): NÃO inclui dotenv_settings (.env)
        - Dev/local: inclui dotenv_settings (.env)
        """
        app_env = os.getenv("APP_ENV", "development").lower()
        is_prod = (
            app_env == "production"
            or "RENDER" in os.environ
            or "RENDER_SERVICE_ID" in os.environ
        )

        if is_prod:
            return (init_settings, env_settings, file_secret_settings)

        return (init_settings, env_settings, dotenv_settings, file_secret_settings)

    # ---------- Ambiente ----------
    APP_ENV: str = Field(default="development")  # development | production
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="DEBUG")

    # CORS_ORIGINS
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000", "http://localhost:5173"],
        alias="CORS_ORIGINS",
    )

    # ---------- Rotas / arquivos ----------
    API_V1_STR: str = "/api/v1"
    DIR_BASE: str = "dados/"
    BASE: str = "catalogo_livros.csv"

    # ---------- Banco ----------
    # Render injeta DATABASE_URL (Config Vars).
    DB_URL: Optional[str] = Field(
        default="postgresql+asyncpg://postgres:134679@localhost:5432/catalogo_livros"
    )
    DATABASE_URL: Optional[str] = Field(default=None)

    DBBaseModel: ClassVar = declarative_base()

    # ---------- JWT ----------
    # Em produção: deve vir do ambiente (Render Config Vars)
    # Em dev: se não vier, gera automaticamente
    JWT_SECRET: Optional[str] = Field(default=None)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias

    @property
    def is_production(self) -> bool:
        return (
            self.APP_ENV.lower() == "production"
            or "RENDER" in os.environ
            or "RENDER_SERVICE_ID" in os.environ
        )

    @property
    def effective_db_url(self) -> str:
        """
        Resolve a URL do banco priorizando:
        1) DATABASE_URL (Render)
        2) DB_URL (local/dev)

        Também converte:
        - postgres://  -> postgresql://
        - postgresql:// -> postgresql+asyncpg://
        """
        raw = self.DATABASE_URL or self.DB_URL
        if not raw:
            raise ValueError("DB_URL/DATABASE_URL não foi definido.")

        if raw.startswith("postgres://"):
            raw = raw.replace("postgres://", "postgresql://", 1)

        if raw.startswith("postgresql://"):
            raw = raw.replace("postgresql://", "postgresql+asyncpg://", 1)

        return raw

    @property
    def sqlalchemy_connect_args(self) -> dict:
        """
        Render Postgres pode exigir SSL dependendo do tipo de conexão.
        Para SQLAlchemy async + asyncpg, 'ssl' em connect_args é compatível.
        """
        if self.is_production and ("RENDER" in os.environ or "RENDER_SERVICE_ID" in os.environ):
            return {"ssl": "require"}
        return {}

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()

            # Aceita JSON: ["https://a.com","https://b.com"]
            if s.startswith("["):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass

            # Aceita CSV: "a,b,c"
            return [item.strip() for item in v.split(",") if item.strip()]

        return v

    @model_validator(mode="after")
    def _validate_env_rules(self):
        # Regras para produção
        if self.is_production:
            if not self.JWT_SECRET:
                raise ValueError(
                    "JWT_SECRET é obrigatório em produção (defina em Render Config Vars)."
                )

            if self.DEBUG is True:
                self.DEBUG = False

            if self.LOG_LEVEL.upper() == "DEBUG":
                self.LOG_LEVEL = "INFO"

        # Regras para dev
        else:
            if not self.JWT_SECRET:
                self.JWT_SECRET = secrets.token_urlsafe(32)

        return self


settings: Settings = Settings()
