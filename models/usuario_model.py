from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from utils.configs import settings


class UsuarioModel(settings.DBBaseModel):
    __tablename__ = "usuarios"

    id: int = Column(Integer, primary_key=True, index=True)
    nome: str = Column(String(256), nullable=False)
    sobrenome: str = Column(String(256), nullable=False)
    email: str = Column(String(256), nullable=False, unique=True)
    senha: str = Column(String(256), nullable=False)
    eh_admin: bool = Column(Boolean, default=False)

    artigos = relationship(
        "ArtigoModel", cascade="all, delete-orphan", back_populates="autor", uselist=True, lazy="joined")
