from pytz import timezone
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from pydantic import EmailStr

from models.usuario_model import UsuarioModel
from utils.configs import settings
from utils.security import verificar_senha
from pydantic import BaseModel
from utils.configs import settings
import logging

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/users/login")

security = HTTPBearer()

logger = logging.getLogger(__name__)


class TokenData:
    """Dados extraídos do JWT token"""

    def __init__(self, sub: str,  is_admin: bool = False):
        self.sub = sub
        self.is_admin = is_admin


# class TokenResponse(BaseModel):
#     """Response com o token JWT"""
#     access_token: str
#     token_type: str = "bearer"
#     expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


async def verifica_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    Valida o JWT token extraído do header Authorization.

    Args:
        credentials: HTTPAuthCredentials automaticamente extraído do header

    Returns:
        TokenData com informações do usuário

    Raises:
        HTTPException: Se o token for inválido ou expirado
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.JWT_SECRET,
                             algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        is_admin: bool = payload.get("is_admin", False)

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: usuário não encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_data = TokenData(sub=username, is_admin=is_admin)

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


async def autenticar_usuario(email: EmailStr, senha: str, db: AsyncSession) -> Optional[UsuarioModel]:
    async with db as session:
        query = select(UsuarioModel).filter(UsuarioModel.email == email)
        result = await session.execute(query)
        usuario: UsuarioModel = result.scalars().unique().one_or_none()

        if not usuario:
            return None
        if not verificar_senha(senha, usuario.senha):
            return None
        return usuario


def _criar_token(tipo_token: str, tempo_vida: timedelta, sub: str, is_admin: bool = False) -> str:
    # https://datatracker.ietf.org/doc/html/rfc7519#section-4.1.3
    payload = {}

    sp = timezone('America/Sao_Paulo')
    expira = datetime.now(tz=sp) + tempo_vida

    payload["type"] = tipo_token

    payload["exp"] = expira

    payload["iat"] = datetime.now(tz=sp)

    payload["sub"] = str(sub)

    payload["is_admin"] = is_admin

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def criar_token_acesso(sub: str, is_admin: bool = False) -> str:
    """ http://jwt.io/introduction/ """
    return _criar_token(
        tipo_token="access_token",
        tempo_vida=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        sub=sub,
        is_admin=is_admin
    )


async def verificar_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Valida token JWT do header Authorization: Bearer <token> e verifica se o usuário é administrador
    """

    if credentials is None:
        logger.error("❌ Credenciais não recebidas")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token não fornecido"
        )

    token = credentials.credentials
    logger.info(f"🔐 Token recebido: {token[:20]}...")

    try:
        # Decodificar token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        logger.info(f"✅ Token válido: {payload.get('sub')}")
        print(payload.get("is_admin"))
        # Verificar se é admin
        if not payload.get("is_admin", False):
            logger.warning(f"❌ Usuário {payload.get('sub')} não é admin")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A função deletar é restrita a Administradores"
            )

        return payload

    except jwt.ExpiredSignatureError:
        logger.error("❌ Token expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except JWTError as e:
        logger.error(f"❌ Token inválido: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou corrompido"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro desconhecido: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao validar token"
        )
