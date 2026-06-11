from unidecode import unidecode


def score_empresa(nome_original: str, titulo_resultado: str) -> int:
    """
    Compara o nome da empresa buscada com o título de um resultado do Google.
    Retorna um score numérico — quanto maior, mais provável que seja a mesma empresa.
    """
    nome_original = unidecode(nome_original.lower())
    titulo_resultado = unidecode(titulo_resultado.lower())

    palavras_nome = {p for p in nome_original.split() if len(p) > 2}
    palavras_titulo = {p for p in titulo_resultado.split() if len(p) > 2}

    score = len(palavras_nome & palavras_titulo)

    primeira_palavra = nome_original.split()[0] if nome_original.split() else ""
    if primeira_palavra and primeira_palavra in palavras_titulo:
        score += 5

    return score