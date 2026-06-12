from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Classe base para todos os models.
    Todo model herda dela para ser reconhecido pelo SQLAlchemy.
    """
    pass