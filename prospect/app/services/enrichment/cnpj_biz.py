from urllib.parse import quote
from time import sleep
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

from app.services.lead_finder.scorer import score_empresa
from app.services.lead_finder.google import criar_driver, get_proxy_from_provider, report_bad_proxy_to_provider


def buscar_cnpj(nome: str) -> str | None:
    """
    Busca o CNPJ no Google usando cnpj.biz, tentando proxies até encontrar.

    Retorna o CNPJ como string ou None se não encontrado.
    """
    while True:
        proxy = get_proxy_from_provider()
        print(f"Usando proxy {proxy} para buscar CNPJ de: {nome}")
        driver = criar_driver(proxy, headless=False)
        try:
            google_search = "https://www.google.com/search?q="
            driver.get(f"{google_search}{quote(nome)} CNPJ BIZ")
            sleep(3)

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

        except Exception as e:
            print(f"Erro na busca com proxy {proxy}: {e}")
            report_bad_proxy_to_provider(proxy)
            print("Tentando novo proxy...")

        finally:
            try:
                driver.quit()
            except Exception:
                pass
