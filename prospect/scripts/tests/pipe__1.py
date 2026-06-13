import os
import requests
from typing import Dict, Any

from app.services.messaging.templates import TEMPLATES  # import correto

#python -m scripts.tests.pipe__1

# URL base da API (use `PROSPECT_API` para alterar)
BASE_URL = os.getenv("PROSPECT_API", "http://localhost:8000")


def deletar_todas_campanhas():
    """Lista campanhas via API e deleta cada uma chamando DELETE /campaigns/{id}.

    Observação: o servidor FastAPI deve estar rodando (por padrão em localhost:8000).
    """
    resp = requests.get(f"{BASE_URL}/campaigns/")
    resp.raise_for_status()
    campanhas = resp.json()
    if not campanhas:
        print("Nenhuma campanha para deletar.")
        return
    deleted = 0
    for c in campanhas:
        cid = c.get("id")
        if cid is None:
            continue
        r = requests.delete(f"{BASE_URL}/campaigns/{cid}")
        if r.status_code in (200, 202, 204):
            deleted += 1
        else:
            print(f"Falha ao deletar campanha {cid}: {r.status_code} {r.text}")
    print(f"{deleted} campanhas deletadas via API.")

def criar_campanha(name: str, query: str, nicho: str = "default") -> Dict[str, Any]:
    """Cria campanha usando o endpoint POST /campaigns/ e retorna o JSON da campanha criada."""
    payload = {"name": name, "query": query, "nicho": nicho}
    resp = requests.post(f"{BASE_URL}/campaigns/", json=payload)
    resp.raise_for_status()
    campanha = resp.json()
    print(f"Campanha '{name}' criada com ID {campanha.get('id')}.")
    return campanha


def adicionar_template_centrus():
    TEMPLATES["prospect_assessoria_empresarial"] = (
    "Olá! Tudo bem?\n\n"
    "Vi que a *$nome_empresa* atua em Fortaleza.\n\n"
    "Uma dúvida: se sua equipe pudesse dedicar menos tempo à busca de potenciais clientes e mais tempo ao fechamento de contratos, isso teria valor para vocês?\n\n"
    "Estamos desenvolvendo uma plataforma que automatiza a identificação de empresas, localização de contatos e abordagem inicial de prospecção.\n\n"
    "O resultado é mais oportunidades comerciais com menos trabalho operacional.\n\n"
    "Faz sentido conversarmos por alguns minutos?"
)
    
    print("Template para 'prospect_assessoria_empresarial' adicionado.")


def main():
    # 1. Apaga todas as campanhas anteriores
    # deletar_todas_campanhas()

    # 2. Adiciona o template customizado
    adicionar_template_centrus()

    # 3. Define uma query combinando nicho + região (exemplo)
    query = 'Assessoria Empresarial "Fortaleza"'

    # 4. Cria a nova campanha com essa query
    campanha = criar_campanha(
        name="prospect_assessoria_empresarial",
        query=query,
        nicho="prospect_assessoria_empresarial"
    )

    # 5. Solicita execução do pipeline via endpoint da API
    campaign_id = campanha.get("id")
    if not campaign_id:
        print("Erro: campanha criada sem ID.")
        return

    run_resp = requests.post(
        f"{BASE_URL}/pipeline/campaigns/{campaign_id}/run",
        json={"instance_name": "teste_local", "enviar": True},
    )

    if run_resp.status_code >= 400:
        print(f"Falha ao agendar pipeline: {run_resp.status_code} {run_resp.text}")
    else:
        print(f"Pipeline agendado para campanha {campaign_id}.")


if __name__ == "__main__":
    main()
