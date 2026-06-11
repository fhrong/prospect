import os
import requests
from typing import Optional

# ──────────────────────────────────────────────
# Configuração
# Defina estas variáveis no seu .env futuramente.
# Por enquanto pode setar direto aqui para testar.
# ──────────────────────────────────────────────
EVOLUTION_BASE_URL = os.getenv("EVOLUTION_BASE_URL", "http://localhost:8080")
EVOLUTION_API_KEY  = os.getenv("EVOLUTION_API_KEY", "sua-chave-aqui")

HEADERS = {
    "Content-Type": "application/json",
    "apikey": EVOLUTION_API_KEY,
}


# ──────────────────────────────────────────────
# INSTÂNCIAS
# Cada cliente do seu SaaS = uma instância própria.
# ──────────────────────────────────────────────

def criar_instancia(nome_instancia: str) -> dict:
    """
    Cria uma instância nova para um cliente.
    Retorna o QR Code que o cliente precisa escanear
    para conectar o WhatsApp dele.

    Uso:
        resultado = criar_instancia("cliente_joao")
        print(resultado["qrcode"]["base64"])  # exibe o QR
    """
    payload = {
        "instanceName": nome_instancia,
        "qrcode": True,
        "integration": "WHATSAPP-BAILEYS",
    }

    resp = requests.post(
        f"{EVOLUTION_BASE_URL}/instance/create",
        json=payload,
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def status_instancia(nome_instancia: str) -> str:
    """
    Retorna o estado da conexão da instância.
    Possíveis valores: 'open' (conectado), 'close' (desconectado), 'connecting'.
    """
    resp = requests.get(
        f"{EVOLUTION_BASE_URL}/instance/connectionState/{nome_instancia}",
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("instance", {}).get("state", "unknown")


def deletar_instancia(nome_instancia: str) -> bool:
    """
    Remove a instância de um cliente (ex: cancelamento do plano).
    """
    resp = requests.delete(
        f"{EVOLUTION_BASE_URL}/instance/delete/{nome_instancia}",
        headers=HEADERS,
        timeout=10,
    )
    return resp.status_code == 200


# ──────────────────────────────────────────────
# MENSAGENS
# ──────────────────────────────────────────────

def enviar_mensagem(
    nome_instancia: str,
    numero: str,
    texto: str,
    delay_segundos: int = 3,
) -> dict:
    """
    Envia uma mensagem de texto para um número.

    - nome_instancia : instância do cliente que está enviando
    - numero         : telefone do lead, ex: "5516999998888"
                       (sem +, com DDI e DDD)
    - texto          : conteúdo da mensagem
    - delay_segundos : simula digitação humana antes de enviar

    Uso:
        enviar_mensagem(
            "cliente_joao",
            "5516999998888",
            "Olá João, vi que a sua empresa..."
        )
    """
    numero = _formatar_numero(numero)

    payload = {
        "number": numero,
        "text": texto,
        "delay": delay_segundos * 1000,  # Evolution usa milissegundos
    }

    resp = requests.post(
        f"{EVOLUTION_BASE_URL}/message/sendText/{nome_instancia}",
        json=payload,
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def verificar_numero(nome_instancia: str, numero: str) -> bool:
    """
    Verifica se o número tem WhatsApp antes de enviar.
    Evita disparos para números inválidos.
    """
    numero = _formatar_numero(numero)

    payload = {"numbers": [numero]}

    resp = requests.post(
        f"{EVOLUTION_BASE_URL}/chat/whatsappNumbers/{nome_instancia}",
        json=payload,
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    dados = resp.json()

    # Retorna True se o primeiro número da lista existe no WhatsApp
    if dados and isinstance(dados, list):
        return dados[0].get("exists", False)

    return False


# ──────────────────────────────────────────────
# WEBHOOK
# Configura para onde a Evolution vai enviar
# as respostas dos leads.
# ──────────────────────────────────────────────

def configurar_webhook(nome_instancia: str, url_webhook: str) -> dict:
    """
    Define a URL que a Evolution vai chamar quando
    o lead responder uma mensagem.

    url_webhook: URL pública da sua API, ex:
        "https://seudominio.com/webhooks/whatsapp"
    """
    payload = {
        "url": url_webhook,
        "webhook_by_events": False,
        "webhook_base64": False,
        "events": [
            "MESSAGES_UPSERT",   # nova mensagem recebida
            "CONNECTION_UPDATE",  # mudança no status da conexão
        ],
    }

    resp = requests.post(
        f"{EVOLUTION_BASE_URL}/webhook/set/{nome_instancia}",
        json=payload,
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


# ──────────────────────────────────────────────
# WEBHOOK HANDLER
# Processa o payload que a Evolution envia
# quando um lead responde.
# ──────────────────────────────────────────────

def processar_webhook(payload: dict) -> Optional[dict]:
    """
    Recebe o payload bruto do webhook da Evolution
    e retorna um dicionário limpo com o que importa.

    Retorna None se não for uma mensagem de texto comum
    (ex: notificação de status, mensagem de grupo, etc).

    Uso na sua API (FastAPI):
        @app.post("/webhooks/whatsapp")
        async def webhook(payload: dict):
            mensagem = processar_webhook(payload)
            if mensagem:
                # classificar com IA, atualizar status do lead...
                pass
    """
    evento = payload.get("event")

    # Só processa mensagens recebidas
    if evento != "messages.upsert":
        return None

    dados = payload.get("data", {})

    # Ignora mensagens enviadas por você (fromMe)
    if dados.get("key", {}).get("fromMe"):
        return None

    # Ignora mensagens de grupos
    numero = dados.get("key", {}).get("remoteJid", "")
    if "@g.us" in numero:
        return None

    texto = (
        dados.get("message", {}).get("conversation")
        or dados.get("message", {}).get("extendedTextMessage", {}).get("text")
    )

    if not texto:
        return None

    return {
        "numero": numero.replace("@s.whatsapp.net", ""),
        "texto": texto.strip(),
        "instancia": payload.get("instance"),
        "timestamp": dados.get("messageTimestamp"),
    }


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _formatar_numero(numero: str) -> str:
    """
    Garante que o número esteja no formato esperado pela Evolution:
    apenas dígitos, com DDI. Ex: "5516999998888"

    Remove +, espaços, hífens e parênteses.
    """
    numero = numero.strip()
    numero = numero.replace("+", "").replace(" ", "")
    numero = numero.replace("-", "").replace("(", "").replace(")", "")

    # Adiciona DDI do Brasil se não tiver
    if len(numero) <= 11:
        numero = "55" + numero

    return numero