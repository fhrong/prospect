from urllib.parse import quote
from time import sleep

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

from app.services.lead_finder.scorer import score_empresa


def buscar_cnpj(driver: uc.Chrome, nome: str) -> str | None:
    """
    Dado o nome de uma empresa, busca o CNPJ no Google usando o site cnpj.biz.
    Retorna o CNPJ como string ou None se não encontrado.
    """
    google_search = "https://www.google.com/search?q="
    driver.get(f"{google_search}{quote(nome)} CNPJ BIZ")
    sleep(1)

    links = driver.find_elements(By.CSS_SELECTOR, 'a[jsname="UWckNb"]')

    melhor_url = None
    melhor_score = -1
    melhor_titulo = None

    for link in links:
        href = link.get_attribute("href")
        if not href or "cnpj.biz/" not in href:
            continue

        try:
            titulo = link.find_element(By.TAG_NAME, "h3").text.strip()
        except Exception:
            continue

        score = score_empresa(nome, titulo)
        if score > melhor_score:
            melhor_score = score
            melhor_url = href
            melhor_titulo = titulo

    if not melhor_url:
        print(f"[cnpj_biz] Não encontrado para: {nome}")
        return None

    print(f"[cnpj_biz] Melhor resultado: {melhor_titulo} (score {melhor_score})")

    cnpj = melhor_url.rstrip("/").split("/")[-1]
    return cnpj