from time import sleep

import requests


def buscar_dados_receita(cnpj: str, nome_fallback: str = "") -> dict | None:
    """
    Consulta a API opencnpj.org com o CNPJ fornecido.
    Retorna um dicionário com os dados da empresa ou None em caso de erro.
    """
    sleep(1)  # respeita o rate-limit da API

    try:
        resp = requests.get(
            f"https://api.opencnpj.org/{cnpj}?dataset=receita",
            timeout=10,
        )
    except Exception as e:
        print(f"[opencnpj] Erro de conexão para CNPJ {cnpj}: {e}")
        return None

    if resp.status_code != 200:
        print(f"[opencnpj] HTTP {resp.status_code} para CNPJ {cnpj}")
        return None

    dados = resp.json()

    telefones = dados.get("telefones", [])
    telefone = None
    if telefones:
        telefone = f"({telefones[0].get('ddd', '')}) {telefones[0].get('numero', '')}"

    return {
        "nome_oficial": dados.get("nome_fantasia") or dados.get("razao_social") or nome_fallback,
        "cnpj": cnpj,
        "telefone": telefone,
        "email": dados.get("email"),
        "cidade": dados.get("municipio"),
        "uf": dados.get("uf"),
    }