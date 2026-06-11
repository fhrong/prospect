from urllib.parse import quote
from time import sleep

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By


def criar_driver() -> uc.Chrome:
    return uc.Chrome(
        options=uc.ChromeOptions(),
        version_main=148,
        headless=True
    )


def buscar_empresas(driver: uc.Chrome, query: str) -> list[str]:
    google_search = "https://www.google.com/search?q="
    driver.get(f"{google_search}{quote(query)}")

    mais_empresas = None
    for _ in range(10):
        botoes = driver.find_elements(By.CLASS_NAME, "jRKCUd")
        if botoes:
            mais_empresas = botoes[0]
            break
        driver.execute_script("window.scrollBy(0, 1000);")
        sleep(0.5)

    if not mais_empresas:
        raise Exception("Botão 'Mais empresas' não encontrado.")

    driver.get(mais_empresas.get_attribute("href"))
    sleep(2)

    nomes = []
    for el in driver.find_elements(By.CSS_SELECTOR, ".dbg0pd .OSrXXb"):
        texto = el.text.strip()
        if texto and texto not in nomes:
            nomes.append(texto)

    return nomes