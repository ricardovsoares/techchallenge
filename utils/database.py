from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from utils.configs import settings

# engine: AsyncEngine = create_async_engine(settings.DB_URL, echo=True)

engine: AsyncEngine = create_async_engine(
    settings.effective_db_url,
    connect_args=settings.sqlalchemy_connect_args,
    echo=True,
    pool_pre_ping=True,
)


Session: AsyncSession = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
    bind=engine
)
