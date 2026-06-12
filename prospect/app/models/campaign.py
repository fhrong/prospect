from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Campaign(Base):
    """
    Representa uma campanha de prospecção.

    Exemplo:
        query = 'Escritório de Contabilidade "Ribeirão Preto"'
        nicho = 'contabilidade'
    """
    __tablename__ = "campaigns"

    id:         Mapped[int]      = mapped_column(primary_key=True)
    name:       Mapped[str]      = mapped_column(String(255))
    query:      Mapped[str]      = mapped_column(String(500))
    nicho:      Mapped[str]      = mapped_column(String(100))
    status:     Mapped[str]      = mapped_column(String(50), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Um campanha tem muitos leads
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="campaign")

    def __repr__(self) -> str:
        return f"<Campaign id={self.id} name={self.name!r} status={self.status}>"