from urllib.parse import quote
from time import sleep
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import requests

# New standard Selenium driver function with detach for debugging
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options

# def criar_driver() -> webdriver.Chrome:
#     options = Options()
#     options.add_experimental_option("detach", True)
#     options.headless = False
#     return webdriver.Chrome(options=options)

PROXY_PROVIDER_URL = "http://localhost:8001"

# Original undetected_chromedriver function (comment while debugging)
def get_proxy_from_provider():
    resp = requests.get(f"{PROXY_PROVIDER_URL}/proxy/best", timeout=10)
    resp.raise_for_status()
    return resp.json()["proxy"]
def report_bad_proxy_to_provider(proxy):
    try:
        requests.post(f"{PROXY_PROVIDER_URL}/proxy/report_bad", json={"proxy": proxy}, timeout=5)
    except Exception as e:
        print(f"Falha ao reportar proxy ruim {proxy}: {e}")
def criar_driver(proxy=None, headless=True):
    options = uc.ChromeOptions()
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    return uc.Chrome(options=options, version_main=148, headless=headless)

def buscar_empresas(query: str) -> list[str]:
    while True:
        proxy = get_proxy_from_provider()
        print(f"Usando proxy {proxy} para buscar empresas...")
        driver = criar_driver(proxy, headless=True)
        try:
            google_search = "https://www.google.com/search?q="
            driver.get(f"{google_search}{quote(query)}")
            sleep(2)
            # Verifica pagina de captcha
            if "sorry/index" in driver.current_url or "recaptcha" in driver.current_url:
                print("CAPTCHA detectado! Reportando proxy e tentando novo proxy...")
                report_bad_proxy_to_provider(proxy)
                driver.quit()
                continue  # tenta novo proxy sem parar
            # Botão "Mais empresas"
            mais_empresas = None
            for _ in range(10):
                botoes = driver.find_elements(By.XPATH, '//*[@id="Odp5De"]/div[1]/div/div/div/div[1]/div[2]/div/div[1]/div[2]/div/h3/div/a')
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
            driver.quit()
            return nomes
        except Exception as e:
            print(f"Erro na busca com proxy {proxy}: {e}")
            try:
                driver.quit()
            except:
                pass
            report_bad_proxy_to_provider(proxy)
            print("Tentando novo proxy...")
            # continuar o loop para tentar novamente com novo proxy
