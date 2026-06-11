from fastapi import FastAPI
from app.database import engine
from app.models import Base
from app.api import campaigns_router, leads_router

# ──────────────────────────────────────────────
# Cria todas as tabelas no banco ao iniciar.
# Futuramente isso será substituído por Alembic (migrations).
# ──────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Prospect API",
    description="Pipeline comercial B2B automatizado — Centris Automation",
    version="0.1.0",
)

app.include_router(campaigns_router)
app.include_router(leads_router)


@app.get("/")
def health_check():
    return {"status": "ok", "produto": "Prospect API"}