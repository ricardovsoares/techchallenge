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

from utils.logger import configura_logger

logger = configura_logger(__name__, "usuarios.log")

router_usuario = APIRouter()


# GET Usuario logado
@router_usuario.get('/logado', response_model=UsuarioSchemaBase, summary="📥 Verifica Token de usuário logado",
                    description="Recupera os dados do usuário autenticado no token JWT.",
                    tags=["Users"],
                    responses={
                        200: {
                            "description": "Dados do usuário autenticado retornados com sucesso",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "id": 1,
                                        "nome": "João",
                                        "sobrenome": "Silva",
                                        "email": "joao@example.com",
                                        "eh_admin": False
                                    }
                                }
                            }
                        },
                        401: {"description": "Token inválido ou expirado"},
                        500: {"description": "Erro ao recuperar dados do usuário"}
                    })
def get_usuario_logado(usuario_logado: UsuarioModel = Depends(get_usuario_atual)):
    """
    Recupera os dados do usuário autenticado no token JWT.

    Fluxo:
    1. Valida e extrai dados do token JWT (via Depends)
    2. Registra o acesso em log
    3. Retorna o objeto do usuário logado

    Returns:
        UsuarioSchemaBase: Dados do usuário autenticado

    Raises:
        HTTPException 500: Erro ao recuperar dados do usuário
    """
    try:
        logger.debug(
            f"Retornando dados do usuário logado: ID {usuario_logado.id}")
        return usuario_logado
    except Exception as e:
        logger.error("Erro ao obter dados do usuário logado", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter dados do usuário logado"
        )


# POST Criar usuário
@router_usuario.post('/signup', status_code=status.HTTP_201_CREATED, response_model=UsuarioSchemaBase, summary="📥 Cadastro de usuário",
                     description="Registra um novo usuário no sistema.",
                     tags=["Users"],
                     responses={
                         201: {
                             "description": "Usuário criado com sucesso",
                             "content": {
                                 "application/json": {
                                     "example": {
                                         "nome": "João",
                                         "sobrenome": "Silva",
                                         "email": "joao@example.com",
                                         "eh_admin": False
                                     }
                                 }
                             }
                         },
                         406: {"description": "Email já existe no sistema"},
                         500: {"description": "Erro ao criar usuário"}
                     })
async def post_usuario(usuario: UsuarioSchemaCreate, db: AsyncSession = Depends(get_session)):
    """
    Registra um novo usuário no sistema.

    Fluxo:
    1. Valida os dados de entrada (nome, sobrenome, email, senha)
    2. Hash da senha usando algoritmo seguro
    3. Cria nova instância de UsuarioModel
    4. Persiste no banco de dados
    5. Retorna o usuário criado

    Args:
        usuario: Dados do novo usuário (UsuarioSchemaCreate)
        db: Sessão de banco de dados assíncrono

    Returns:
        UsuarioSchemaBase: Dados do usuário criado

    Raises:
        HTTPException 406: Email já existe no sistema (violação de constraint)
        HTTPException 500: Erro ao criar usuário (banco ou servidor)
    """
    try:
        logger.info(f"/signup", "POST", {usuario.email})
        novo_usuario: UsuarioModel = UsuarioModel(
            nome=usuario.nome, sobrenome=usuario.sobrenome, email=usuario.email, eh_admin=usuario.eh_admin, senha=gerar_hash_senha(usuario.senha))
        logger.debug(f"Novo usuário preparado: {usuario.email}")
        async with db as session:
            try:
                logger.info(f"/signup", "POST", {usuario.email})
                session.add(novo_usuario)
                await session.commit()
                return novo_usuario
            except IntegrityError:
                logger.warning(
                    f"Tentativa de criação com email existente: {usuario.email}")
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                    detail='Já existe um usuário com este e-mail cadastrado.')
            except HTTPException:
                raise
            except Exception as e:
                logger.info("criação de usuário %s", str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao criar usuário"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("criação de usuário %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar usuário"
        )


# GET Todos os usuários
@router_usuario.get('/', response_model=List[UsuarioSchemaBase], summary="📋 Listar usuário",
                    description="Recupera todos os usuários registrados no sistema.",
                    tags=["Users"],
                    responses={
                        200: {
                            "description": "Lista de usuários retornada com sucesso",
                            "content": {
                                "application/json": {
                                    "example": [
                                        {
                                            "id": 1,
                                            "nome": "João",
                                            "sobrenome": "Silva",
                                            "email": "joao@example.com",
                                            "eh_admin": False
                                        },
                                        {
                                            "id": 2,
                                            "nome": "Maria",
                                            "sobrenome": "Santos",
                                            "email": "maria@example.com",
                                            "eh_admin": True
                                        }
                                    ]
                                }
                            }
                        },
    401: {"description": "Token inválido ou não fornecido"},
    500: {"description": "Erro ao listar usuários"}
})
async def get_usuarios(db: AsyncSession = Depends(get_session)):
    """
    Recupera todos os usuários registrados no sistema.

    Fluxo:
    1. Conecta ao banco de dados
    2. Executa query SELECT para obter todos os UsuarioModel
    3. Remove duplicatas (unique())
    4. Retorna lista com todos os usuários

    Args:
        db: Sessão de banco de dados assíncrono

    Returns:
        List[UsuarioSchemaBase]: Lista com todos os usuários do sistema

    Raises:
        HTTPException 500: Erro ao consultar ou processar dados dos usuários
    """
    try:
        async with db as session:
            logger.info("%s %s", "/", "GET")
            query = select(UsuarioModel)
            result = await session.execute(query)
            usuarios: List[UsuarioModel] = result.scalars().unique().all()
            logger.debug(f"Total de usuários encontrados: {len(usuarios)}")
            return usuarios
    except Exception as e:
        # logger.error("listagem de usuários: %s", str(e))
        logger.exception("listagem de usuários")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar usuários"
        )


# GET Usuario
@router_usuario.get('/{usuario_id}', response_model=UsuarioSchemaBase, status_code=status.HTTP_200_OK,
                    summary="🔍 Pesquisar usuário por ID",
                    description="Recupera dados de um usuário específico pelo seu ID.",
                    tags=["Users"],
                    responses={
                        200: {
                            "description": "Usuário encontrado",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "id": 1,
                                        "nome": "João",
                                        "sobrenome": "Silva",
                                        "email": "joao@example.com",
                                        "eh_admin": False
                                    }
                                }
                            }
                        },
                        401: {"description": "Token inválido ou não fornecido"},
                        404: {"description": "Usuário não encontrado"},
                        500: {"description": "Erro ao consultar banco de dados"}
                    })
async def get_usuario(usuario_id: int, db: AsyncSession = Depends(get_session)):
    """
    Recupera dados de um usuário específico pelo seu ID.

    Fluxo:
    1. Valida o ID do usuário (parâmetro da URL)
    2. Conecta ao banco de dados
    3. Executa query WHERE UsuarioModel.id = usuario_id
    4. Se encontrado: retorna os dados
    5. Se não encontrado: lança exceção 404

    Args:
        usuario_id: ID do usuário a ser buscado
        db: Sessão de banco de dados assíncrono

    Returns:
        UsuarioSchemaBase: Dados do usuário encontrado

    Raises:
        HTTPException 404: Usuário não encontrado (ID inválido)
        HTTPException 500: Erro ao consultar banco de dados
    """
    try:
        async with db as session:
            query = select(UsuarioModel).filter(UsuarioModel.id == usuario_id)
            result = await session.execute(query)
            usuario: UsuarioSchemaBase = result.scalars().unique().one_or_none()
            if usuario:
                logger.debug(f"Usuário encontrado: ID {usuario_id}")
                return usuario
            else:
                logger.warning(
                    f"Tentativa de acesso a usuário inexistente: ID {usuario_id}")
                raise HTTPException(detail='Usuário não encontrado.',
                                    status_code=status.HTTP_404_NOT_FOUND)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Obtenção de usuário", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter usuário"
        )


# PUT Usuario
@router_usuario.put('/{usuario_id}', response_model=UsuarioSchemaBase, status_code=status.HTTP_200_OK,
                    summary="📥 Atualizar usuário",
                    description="Permite que o usuário ou admin atualize seus dados",
                    tags=["Users"],
                    responses={
                        200: {
                            "description": "Usuário atualizado com sucesso",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "id": 1,
                                        "nome": "João Atualizado",
                                        "sobrenome": "Silva",
                                        "email": "joao@example.com",
                                        "eh_admin": False
                                    }
                                }
                            }
                        },
                        401: {"description": "Token inválido ou não fornecido"},
                        404: {"description": "Usuário não encontrado"},
                        500: {"description": "Erro ao atualizar banco de dados"}
                    })
async def put_usuario(usuario_id: int, usuario: UsuarioSchemaUpdate, db: AsyncSession = Depends(get_session)):
    """
    Atualiza informações de um usuário específico.

    Fluxo:
    1. Valida o ID do usuário
    2. Conecta ao banco de dados
    3. Busca o usuário pelo ID
    4. Se encontrado:
       - Atualiza campos fornecidos (nome, sobrenome, email, eh_admin)
       - Ignora campos não fornecidos (None)
       - Persiste as alterações
       - Retorna o usuário atualizado
    5. Se não encontrado: lança exceção 404

    Args:
        usuario_id: ID do usuário a ser atualizado
        usuario: Dados a serem atualizados (UsuarioSchemaUpdate)
        db: Sessão de banco de dados assíncrono

    Returns:
        UsuarioSchemaBase: Dados do usuário após atualização

    Raises:
        HTTPException 404: Usuário não encontrado (ID inválido)
        HTTPException 500: Erro ao atualizar banco de dados
    """
    try:
        async with db as session:
            logger.info(
                f"Usuário {usuario_id} atualizado. Campos:")
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
                await session.commit()
                return usuario_update
            else:
                logger.warning(
                    f"Tentativa de atualizar usuário inexistente: ID {usuario_id}")
                raise HTTPException(detail='Usuário não encontrado.',
                                    status_code=status.HTTP_404_NOT_FOUND)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("atualização de usuário", e, usuario_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar usuário"
        )


# DELETE Deletar usuário
@router_usuario.delete('/{usuario_id}', status_code=status.HTTP_204_NO_CONTENT, summary="📝 Deleção de um usuário",
                       description="Realiza a deleção de um usuário. Apenas para usuários Administradores",
                       tags=["Users"],
                       responses={
                           204: {"description": "Usuário deletado com sucesso"},
                           401: {"description": "Token inválido ou não fornecido"},
                           403: {"description": "Acesso negado: apenas admins podem deletar"},
                           404: {"description": "Usuário não encontrado"},
                           500: {"description": "Erro ao deletar do banco de dados"}
                       })
async def delete_usuario(usuario_id: int, db: AsyncSession = Depends(get_session), usuario_atual: TokenData = Depends(verificar_admin)):
    """
    Remove um usuário do sistema (exclusivo para administradores).

    Fluxo:
    1. Valida se o usuário logado é administrador (via Depends)
    2. Valida o ID do usuário a deletar
    3. Conecta ao banco de dados
    4. Busca o usuário pelo ID
    5. Se encontrado:
       - Remove da base de dados
       - Registra a ação (admin que deletou + ID do deletado)
       - Retorna 204 No Content
    6. Se não encontrado: lança exceção 404

    Args:
        usuario_id: ID do usuário a ser deletado
        db: Sessão de banco de dados assíncrono
        usuario_atual: TokenData do admin autenticado (valida privilégios)

    Returns:
        Response: 204 No Content (sem corpo)

    Raises:
        HTTPException 403: Usuário logado não é administrador
        HTTPException 404: Usuário a deletar não encontrado
        HTTPException 500: Erro ao deletar do banco de dados
    """
    try:
        logger.info(f"Deleção solicitada por admin: ID {usuario_atual}")
        async with db as session:
            query = select(UsuarioModel).filter(UsuarioModel.id == usuario_id)
            result = await session.execute(query)
            usuario_delete: UsuarioSchemaBase = result.scalars().unique().one_or_none()
            if usuario_delete:
                await session.delete(usuario_delete)
                await session.commit()
                logger.warning(
                    f"Usuário {usuario_id} deletado")
                return Response(status_code=status.HTTP_204_NO_CONTENT)
            else:
                logger.warning(
                    f"Tentativa de deletar usuário inexistente: ID {usuario_id}")
                raise HTTPException(detail='Usuário não encontrado.',
                                    status_code=status.HTTP_404_NOT_FOUND)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"deleção de usuário", str(e), {usuario_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao deletar usuário"
        )


# POST Login
@router_usuario.post('/login', summary="📥 Efetuar Login do usuário",
                     description="Realiza a autenticação do usuário",
                     tags=["Users"],
                     responses={
                         200: {
                             "description": "Login bem-sucedido",
                             "content": {
                                 "application/json": {
                                     "example": {
                                         "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                         "token_type": "bearer"
                                     }
                                 }
                             }
                         },
                         400: {"description": "Email ou senha incorretos"},
                         500: {"description": "Erro ao processar autenticação"}
                     })
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)):
    """
    Autentica um usuário e emite um token JWT para futuras requisições.

    Fluxo:
    1. Recebe credenciais (email via username + senha) do formulário
    2. Valida as credenciais contra o banco de dados
    3. Se credenciais válidas:
       - Gera token JWT com ID e status de admin
       - Registra login bem-sucedido
       - Retorna token de acesso
    4. Se credenciais inválidas: lança exceção 400

    Args:
        form_data: Objeto OAuth2PasswordRequestForm com username (email) e password (senha)
        db: Sessão de banco de dados assíncrono

    Returns:
        JSONResponse: {"access_token": "<JWT>", "token_type": "bearer"}

    Raises:
        HTTPException 400: Email ou senha incorretos
        HTTPException 500: Erro ao processar autenticação ou gerar token
    """
    try:
        logger.info(f"/login", "POST", {form_data.username})
        usuario = await autenticar_usuario(email=form_data.username, senha=form_data.password, db=db)
        if not usuario:
            logger.warning(
                f"Tentativa de login com credenciais inválidas: {form_data.username}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='Email ou Senha incorretos.')
        token_acesso = criar_token_acesso(
            sub=usuario.id, is_admin=usuario.eh_admin)
        logger.info(f"Login bem-sucedido: Usuário ID {usuario.id}")
        return JSONResponse(content={"access_token": token_acesso, "token_type": "bearer"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"autenticação/login", str(e), {form_data.username})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao realizar login"
        )
