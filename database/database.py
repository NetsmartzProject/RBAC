from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from config.pydantic_config import settings


SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
# SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:root@localhost:5432/Multi_Tenancy_Database"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL,echo=True)

session = async_sessionmaker(
    autoflush=False,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    bind=engine,
)


async def get_db():
    async with session() as db:
        try:
            yield db
        finally:
            await db.close()



