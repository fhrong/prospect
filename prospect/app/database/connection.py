import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# ──────────────────────────────────────────────
# URL de conexão com o PostgreSQL.
# Futuramente mova para um arquivo .env.
# ──────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://prospect:prospect123@localhost:5432/prospect",
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency do FastAPI.
    Abre uma sessão do banco para cada request e fecha ao terminar.

    Uso nas rotas:
        def minha_rota(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()