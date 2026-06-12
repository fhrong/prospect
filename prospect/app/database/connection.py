import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://prospect:prospect123@localhost:5433/prospect",
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# Remova ou comente as linhas temporárias problemáticas
# print(DATABASE_URL)
# DATABASE_URL = os.getenv(...)  # <--- Remover esta linha
# print("DATABASE_URL =", DATABASE_URL)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
