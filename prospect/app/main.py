from fastapi import FastAPI
from app.database import engine
from app.models import Base
from app.api import campaigns_router, leads_router
from workers.proxy_provider import router as proxy_provider_router
#uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


# Cria as tabelas no banco
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Prospect API",
    description="Pipeline comercial B2B automatizado — Centris Automation",
    version="0.1.0",
)

# Inclui os routers da API
app.include_router(campaigns_router)
app.include_router(leads_router)
app.include_router(proxy_provider_router)


@app.get("/")
def health_check():
    return {"status": "ok", "produto": "Prospect API"}
