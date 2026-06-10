from urllib.parse import quote
from time import sleep
from unidecode import unidecode
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import requests


google_search = "https://www.google.com/search?q="

query = quote(
    'Escritório de Contabilidade "Ribeirão Preto"'
)

def score_empresa(nome_original, titulo_resultado):
    nome_original = unidecode(
        nome_original.lower()
    )

    titulo_resultado = unidecode(
        titulo_resultado.lower()
    )

    palavras_nome = {
        p
        for p in nome_original.split()
        if len(p) > 2
    }

    palavras_titulo = {
        p
        for p in titulo_resultado.split()
        if len(p) > 2
    }

    score = len(
        palavras_nome &
        palavras_titulo
    )

    primeira_palavra = (
        nome_original.split()[0]
        if nome_original.split()
        else ""
    )

    if (
        primeira_palavra and
        primeira_palavra in palavras_titulo
    ):
        score += 5

    return score


driver = uc.Chrome(
    options=uc.ChromeOptions(),
    version_main=148
)

driver.get(
    f"{google_search}{query}"
)

mais_empresas = None

for _ in range(10):

    botoes = driver.find_elements(
        By.CLASS_NAME,
        "jRKCUd"
    )

    if botoes:
        mais_empresas = botoes[0]
        break

    driver.execute_script(
        "window.scrollBy(0, 1000);"
    )

    sleep(0.5)

if not mais_empresas:
    raise Exception(
        "'Mais empresas' button not found."
    )

driver.get(
    mais_empresas.get_attribute("href")
)

sleep(2)

nomes = []

for el in driver.find_elements(
    By.CSS_SELECTOR,
    ".dbg0pd .OSrXXb"
):
    texto = el.text.strip()

    if texto and texto not in nomes:
        nomes.append(texto)

print("\nEMPRESAS:")
print(nomes)

# nome -> cnpj
empresas = {}

for nome in nomes:

    print(
        f"\nBuscando CNPJ de: {nome}"
    )

    driver.get(
        f"{google_search}{quote(nome)} CNPJ BIZ"
    )

    sleep(1)

    links = driver.find_elements(
        By.CSS_SELECTOR,
        'a[jsname="UWckNb"]'
    )

    melhor_url = None
    melhor_score = -1
    melhor_titulo = None

    for link in links:

        href = link.get_attribute(
            "href"
        )

        if (
            not href or
            "cnpj.biz/" not in href
        ):
            continue

        try:

            titulo = link.find_element(
                By.TAG_NAME,
                "h3"
            ).text.strip()

        except:
            continue

        score = score_empresa(
            nome,
            titulo
        )

        if score > melhor_score:

            melhor_score = score
            melhor_url = href
            melhor_titulo = titulo

    if not melhor_url:

        print(
            f"CNPJ Biz não encontrado para {nome}"
        )

        empresas[nome] = {
            "cnpj": None,
            "telefone": None
        }

        continue

    print(
        f"Melhor resultado: {melhor_titulo}"
    )

    print(
        f"Score: {melhor_score}"
    )

    print(
        f"URL: {melhor_url}"
    )

    cnpj = (
        melhor_url
        .rstrip("/")
        .split("/")[-1]
    )

    empresas[nome] = {
        "cnpj": cnpj,
        "telefone": None
    }

print("\nCNPJS ENCONTRADOS:")

for nome, dados in empresas.items():

    print(
        nome,
        "=>",
        dados["cnpj"]
    )


# ====================================
# BUSCA DADOS RECEITA
# ====================================

for nome, dados in list(empresas.items()):

    sleep(1)

    cnpj = dados["cnpj"]

    if not cnpj:
        continue

    try:

        resp = requests.get(
            f"https://api.opencnpj.org/{cnpj}?dataset=receita",
            timeout=10
        )

        if resp.status_code != 200:

            print(
                f"Erro HTTP {resp.status_code} em {nome}"
            )

            continue

        dados_json = resp.json()

        telefones = dados_json.get(
            "telefones",
            []
        )

        telefone = None

        if telefones:

            telefone = (
                f"({telefones[0].get('ddd', '')}) "
                f"{telefones[0].get('numero', '')}"
            )

        nome_oficial = (
            dados_json.get("nome_fantasia")
            or dados_json.get("razao_social")
            or nome
        )

        empresas[nome] = {
            "nome_original": nome,
            "nome_oficial": nome_oficial,
            "cnpj": cnpj,
            "telefone": telefone,
            "email": dados_json.get("email"),
            "cidade": dados_json.get("municipio"),
            "uf": dados_json.get("uf"),
        }

        print(
            f"{nome_oficial} | "
            f"{cnpj} | "
            f"{telefone}"
        )

    except Exception as e:

        print(
            f"Erro em {nome}: {e}"
        )

# ====================================
# RESULTADO FINAL
# ====================================

print("\n\nRESULTADO FINAL\n")

for _, dados in empresas.items():

    print(
        f"Nome Original: {dados.get('nome_original')}"
    )

    print(
        f"Nome Oficial: {dados.get('nome_oficial')}"
    )

    print(
        f"CNPJ: {dados.get('cnpj')}"
    )

    print(
        f"Telefone: {dados.get('telefone')}"
    )

    print(
        f"Email: {dados.get('email')}"
    )

    print(
        f"Cidade: {dados.get('cidade')}"
    )

    print(
        f"UF: {dados.get('uf')}"
    )

    print("-" * 60)

try:
    driver.quit()
except:
    pass