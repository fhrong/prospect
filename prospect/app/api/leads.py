from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Lead, Campaign

router = APIRouter(prefix="/campaigns", tags=["leads"])


# ── Schemas ────────────────────────────────────────────────────

class LeadResponse(BaseModel):
    id:            int
    nome_original: str | None
    nome_oficial:  str | None
    cnpj:          str | None
    telefone:      str | None
    email:         str | None
    cidade:        str | None
    uf:            str | None
    status:        str

    model_config = {"from_attributes": True}


class LeadStatusUpdate(BaseModel):
    status: str  # NEW, ENRICHED, CONTACTED, REPLIED, INTERESTED, NEGATIVE, MEETING_BOOKED


# ── Rotas ──────────────────────────────────────────────────────

@router.get("/{campaign_id}/leads", response_model=list[LeadResponse])
def listar_leads(
    campaign_id: int,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Retorna os leads de uma campanha.
    Aceita filtro por status: ?status=INTERESTED
    """
    campanha = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campanha:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")

    query = db.query(Lead).filter(Lead.campaign_id == campaign_id)
    if status:
        query = query.filter(Lead.status == status.upper())

    return query.all()

@router.patch("/{campaign_id}/leads/{lead_id}", response_model=LeadResponse)
def atualizar_status_lead(
    campaign_id: int,
    lead_id: int,
    payload: LeadStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Atualiza o status de um lead.

    PATCH /campaigns/1/leads/42
    { "status": "INTERESTED" }
    """
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.campaign_id == campaign_id,
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado.")

    lead.status = payload.status.upper()
    db.commit()
    db.refresh(lead)
    return lead