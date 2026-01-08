from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError
from pydantic import BaseModel

from utils.database import Session
from utils.auth import oauth2_scheme
from utils.configs import settings
from models.usuario_model import UsuarioModel


class TokenData(BaseModel):
    username: Optional[str] = None


async def get_session() -> AsyncGenerator:
    session: AsyncSession = Session()

    try:
        yield session
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()


async def get_usuario_atual(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)) -> UsuarioModel:
    # A criação da variável com : faz a tipagem ao invés de atribuir um valor direto, é como dizer
    # "Vou criar uma variável chamada credentials_exception que será do tipo HTTPException,
    # e vou armazenar nela um objeto HTTPException"
    # Type Hint = Anotalção de Tipo
    # Criei essa variável para reutilizá-la no bloco try/except
    credentials_exception: HTTPException = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False}
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data: TokenData = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    async with db as session:
        query = select(UsuarioModel).filter(
            UsuarioModel.id == int(token_data.username))
        result = await session.execute(query)
        usuario: UsuarioModel = result.scalars().unique().one_or_none()

        if usuario is None:
            raise credentials_exception

        return usuario
