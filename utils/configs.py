from typing import List, ClassVar
from pydantic_settings import BaseSettings
# from sqlalchemy.ext.declarative import declarative_base


class Settings(BaseSettings):
    """
    Configurações gerais da aplicação
    """
    API_V1_STR: str = "/api/v1"
    DIR_BASE: str = "dados/"
    BASE: str = "catalogo_livros.csv"
    # DB_URL: str = "postgresql+asyncpg://postgres:134679@localhost:5432/livros"
    # DBBaseModel: ClassVar = declarative_base()

    JWT_SECRET: str = ""
    """
        Chave secreta para assinar os tokens JWT.
        Pode ser gerada usando o comando:
        openssl rand -hex 32

        OUTRO MÉTODO PARA GERAR UMA CHAVE SECRETA USANDO PYTHON:

        import secrets
        token: str = secrets.token_urlsafe(32)
        token
    """
    JWT_ALGORITHM: str = "HS256"
    # 60 minutos * 24 horas * 7 dias = 1 Semana
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias

    class Config:
        case_sensitive = True


settings: Settings = Settings()
