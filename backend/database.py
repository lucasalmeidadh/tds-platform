import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env que está na raiz do projeto
load_dotenv()

# Pega a URL de conexão completa do .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Cria o "motor" de conexão com o banco de dados
engine = create_async_engine(DATABASE_URL)

# Cria um "fabricante de sessões" que usaremos para interagir com o banco
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Cria uma classe Base que nossos modelos de tabela vão herdar
class Base(DeclarativeBase):
    pass

# Função para criar as tabelas no banco de dados (se não existirem)
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)