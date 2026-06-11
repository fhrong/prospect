from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Campaign, Lead

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


# ── Schemas (o que a API recebe e retorna) ─────────────────────

class CampaignCreate(BaseModel):
    name:  str
    query: str
    nicho: str = "default"


class CampaignResponse(BaseModel):
    id:     int
    name:   str
    query:  str
    nicho:  str
    status: str

    model_config = {"from_attributes": True}


# ── Rotas ──────────────────────────────────────────────────────

@router.post("/", response_model=CampaignResponse, status_code=201)
def criar_campanha(payload: CampaignCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova campanha.

    POST /campaigns
    {
        "name": "Contabilidade Ribeirão Preto",
        "query": "Escritório de Contabilidade \"Ribeirão Preto\"",
        "nicho": "contabilidade"
    }
    """
    campanha = Campaign(
        name=payload.name,
        query=payload.query,
        nicho=payload.nicho,
        status="PENDING",
    )
    db.add(campanha)
    db.commit()
    db.refresh(campanha)
    return campanha


@router.get("/", response_model=list[CampaignResponse])
def listar_campanhas(db: Session = Depends(get_db)):
    """Retorna todas as campanhas."""
    return db.query(Campaign).all()


@router.get("/{campaign_id}", response_model=CampaignResponse)
def buscar_campanha(campaign_id: int, db: Session = Depends(get_db)):
    """Retorna uma campanha pelo ID."""
    campanha = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campanha:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    return campanha


@router.delete("/{campaign_id}", status_code=204)
def deletar_campanha(campaign_id: int, db: Session = Depends(get_db)):
    """Deleta uma campanha e todos os leads dela."""
    campanha = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campanha:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
    db.delete(campanha)
    db.commit()