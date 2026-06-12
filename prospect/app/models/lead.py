from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Lead(Base):
    """
    Representa um lead dentro de uma campanha.

    Ciclo de status:
        NEW → ENRICHED → CONTACTED → REPLIED → INTERESTED → MEETING_BOOKED
                                             ↘ NEEDS_FOLLOWUP
                                             ↘ NEGATIVE
    """
    __tablename__ = "leads"

    id:           Mapped[int]           = mapped_column(primary_key=True)
    campaign_id:  Mapped[int]           = mapped_column(ForeignKey("campaigns.id"))

    # Dados básicos
    nome_original: Mapped[str | None]   = mapped_column(String(255))
    nome_oficial:  Mapped[str | None]   = mapped_column(String(255))
    cnpj:          Mapped[str | None]   = mapped_column(String(20))
    telefone:      Mapped[str | None]   = mapped_column(String(30))
    email:         Mapped[str | None]   = mapped_column(String(255))
    cidade:        Mapped[str | None]   = mapped_column(String(100))
    uf:            Mapped[str | None]   = mapped_column(String(2))

    # Controle de pipeline
    status:        Mapped[str]          = mapped_column(String(50), default="NEW")
    ultima_mensagem: Mapped[str | None] = mapped_column(String(1000))
    created_at:    Mapped[datetime]     = mapped_column(DateTime, default=func.now())
    updated_at:    Mapped[datetime]     = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relacionamento com a campanha
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="leads")

    def __repr__(self) -> str:
        return f"<Lead id={self.id} nome={self.nome_oficial!r} status={self.status}>"