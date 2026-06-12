import os
import shutil
import subprocess
import sys
import time

def kill_process_by_name(name):
    try:
        # Força o fim do processo pelo nome usando taskkill (Windows)
        subprocess.run(["taskkill", "/f", "/im", name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Processo '{name}' finalizado com sucesso.")
    except subprocess.CalledProcessError:
        print(f"Nenhum processo '{name}' ativo ou erro ao finalizar.")

def remove_undetected_chromedriver_cache():
    path = os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\undetected_chromedriver")
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            print(f"Pasta {path} removida com sucesso.")
        except Exception as e:
            print(f"Erro ao remover a pasta {path}: {e}")
    else:
        print(f"Pasta {path} não existe, nada a remover.")

def main():
    print("Iniciando limpeza do ambiente ChromeDriver...")
    kill_process_by_name("chromedriver.exe")
    kill_process_by_name("chrome.exe")
    time.sleep(1)  # Pequena pausa para garantir fechamento
    remove_undetected_chromedriver_cache()
    print("Limpeza concluída. Agora você pode rodar o scraper sem erros.")

if __name__ == "__main__":
    main()
