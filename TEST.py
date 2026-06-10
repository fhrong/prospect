from urllib.parse import quote
from time import sleep
from unidecode import unidecode
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


driver = uc.Chrome(
    options=uc.ChromeOptions(),
    version_main=148
)


driver.get(
    "https://solucoes.receita.fazenda.gov.br/Servicos/cnpjreva/"
)

sleep(2)
sleep(2)
campo_cnpj = driver.find_element(
    By.XPATH,
    '//*[@id="alert-cnpj"]/div/input'
)

# checkbox = driver.find_element(
#     By.XPATH,
#     '//*[@id="checkbox"]'
# )

consultar_btn = driver.find_element(
    By.XPATH,
    '//*[@id="app"]/app-emissao-comprovante-inscricao/div/div/div/div[3]/div/button[1]'
)



campo_cnpj.send_keys(
    "55190305000103"
)

campo_cnpj.send_keys(
    Keys.TAB
)

sleep(1)

driver.switch_to.active_element.send_keys(
    Keys.SPACE
)
sleep(1)

consultar_btn.click()