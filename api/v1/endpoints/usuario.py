from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from models.usuario_model import UsuarioModel
from schema.usuario_schema import UsuarioSchemaBase, UsuarioSchemaCreate, UsuarioSchemaUpdate
from utils.deps import get_session, get_usuario_atual
from utils.security import gerar_hash_senha, verificar_senha
from utils.auth import criar_token_acesso, autenticar_usuario
from utils.auth import verificar_admin, TokenData

router_usuario = APIRouter()


# GET Usuario logado
@router_usuario.get('/logado', response_model=UsuarioSchemaBase)
def get_usuario_logado(usuario_logado: UsuarioModel = Depends(get_usuario_atual)):
    return usuario_logado


# POST Criar usuário
@router_usuario.post('/signup', status_code=status.HTTP_201_CREATED, response_model=UsuarioSchemaBase)
async def post_usuario(usuario: UsuarioSchemaCreate, db: AsyncSession = Depends(get_session)):
    novo_usuario: UsuarioModel = UsuarioModel(
        nome=usuario.nome, sobrenome=usuario.sobrenome, email=usuario.email, eh_admin=usuario.eh_admin, senha=gerar_hash_senha(usuario.senha))
    async with db as session:
        try:
            session.add(novo_usuario)
            await session.commit()
            return novo_usuario
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                detail='Já existe um usuário com este e-mail cadastrado.')


# GET Todos os usuários
@router_usuario.get('/', response_model=List[UsuarioSchemaBase])
async def get_usuarios(db: AsyncSession = Depends(get_session)):
    async with db as session:
        query = select(UsuarioModel)
        result = await session.execute(query)
        usuarios: List[UsuarioModel] = result.scalars().unique().all()
        return usuarios


# GET Usuario e seus artigos
@router_usuario.get('/{usuario_id}', response_model=UsuarioSchemaBase, status_code=status.HTTP_200_OK)
async def get_usuario(usuario_id: int, db: AsyncSession = Depends(get_session)):
    async with db as session:
        query = select(UsuarioModel).filter(UsuarioModel.id == usuario_id)
        result = await session.execute(query)
        usuario: UsuarioSchemaBase = result.scalars().unique().one_or_none()
        if usuario:
            return usuario
        else:
            raise HTTPException(detail='Usuário não encontrado.',
                                status_code=status.HTTP_404_NOT_FOUND)


# PUT Usuario
@router_usuario.put('/{usuario_id}', response_model=UsuarioSchemaBase, status_code=status.HTTP_200_OK)
async def put_usuario(usuario_id: int, usuario: UsuarioSchemaUpdate, db: AsyncSession = Depends(get_session)):
    async with db as session:
        query = select(UsuarioModel).filter(UsuarioModel.id == usuario_id)
        result = await session.execute(query)
        usuario_update: UsuarioSchemaBase = result.scalars().unique().one_or_none()
        if usuario_update:
            if usuario.nome:
                usuario_update.nome = usuario.nome
            if usuario.sobrenome:
                usuario_update.sobrenome = usuario.sobrenome
            if usuario.email:
                usuario_update.email = usuario.email
            if usuario.eh_admin is not None:
                usuario_update.eh_admin = usuario.eh_admin
            # if usuario.senha:
            #     usuario_update.senha = gerar_hash_senha(usuario.senha)
            await session.commit()
            return usuario_update
        else:
            raise HTTPException(detail='Usuário não encontrado.',
                                status_code=status.HTTP_404_NOT_FOUND)


# DELETE Deletar usuário
@router_usuario.delete('/{usuario_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(usuario_id: int, db: AsyncSession = Depends(get_session), usuario_atual: TokenData = Depends(verificar_admin)):
    async with db as session:
        query = select(UsuarioModel).filter(UsuarioModel.id == usuario_id)
        result = await session.execute(query)
        usuario_delete: UsuarioSchemaBase = result.scalars().unique().one_or_none()
        if usuario_delete:
            await session.delete(usuario_delete)
            await session.commit()
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            raise HTTPException(detail='Usuário não encontrado.',
                                status_code=status.HTTP_404_NOT_FOUND)


# POST Login
@router_usuario.post('/login')
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)):
    usuario = await autenticar_usuario(email=form_data.username, senha=form_data.password, db=db)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Email ou Senha incorretos.')
    token_acesso = criar_token_acesso(
        sub=usuario.id, is_admin=usuario.eh_admin)
    return JSONResponse(content={"access_token": token_acesso, "token_type": "bearer"})
