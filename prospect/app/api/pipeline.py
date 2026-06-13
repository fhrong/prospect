from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.pipeline import rodar_pipeline

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class PipelineRunRequest(BaseModel):
    instance_name: str
    enviar: bool = True


@router.post("/campaigns/{campaign_id}/run", status_code=202)
def run_pipeline(
    campaign_id: int,
    payload: PipelineRunRequest,
    background_tasks: BackgroundTasks,
):
    """Agenda a execução do pipeline para uma campanha.

    - `instance_name`: nome da instância usada por `verificar_numero`/`enviar_mensagem`.
    - `enviar`: se True envia mensagens; se False apenas realiza busca e enriquecimento.
    """
    # Agenda execução em background para não bloquear a requisição
    background_tasks.add_task(rodar_pipeline, campaign_id, payload.instance_name, payload.enviar)
    return {"status": "scheduled", "campaign_id": campaign_id}
