ATUALIZACAO DO CODIGO
Web scraper para Skokka - MODO DE DEPURAÇÃO v2

Este script foi aprimorado para esperar que o conteúdo dinâmico (os anúncios)
seja carregado antes de salvar o HTML para análise.
"""
from __future__ import annotations

import time
import logging

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# --- FUNÇÃO DE DEPURAÇÃO ---
def save_debug_html(driver: webdriver.Chrome, filename: str = "debug.html"):
    """Salva o código-fonte da página atual em um arquivo HTML."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info(f"✅ HTML de depuração salvo com sucesso em '{filename}'.")
    except Exception as e:
        logging.error(f"Falha ao salvar o HTML de depuração: {e}")

# --- FUNÇÕES DO SCRAPER ---
def initialise_driver(headless: bool = True) -> webdriver.Chrome:
    """Configura e inicializa o driver do Chrome."""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--lang=pt-BR")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    if headless:
        options.add_argument("--headless=new")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def handle_initial_popups(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    """Lida com pop-ups de idade e cookies de forma segura."""
    selectors = [
        (By.CSS_SELECTOR, "button.b1"),
        (By.XPATH, "//button[contains(., 'Aceitar Todos Os Cookies')]"),
    ]
    for by, selector in selectors:
        try:
            button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((by, selector)))
            button.click()
            logging.info(f"Pop-up aceito com o seletor: {selector}")
            time.sleep(1.5)
        except TimeoutException:
            logging.warning(f"Pop-up não encontrado com o seletor: {selector}")

# --- FUNÇÃO PRINCIPAL ---
def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    
    start_url = "https://br.skokka.com/encontros/sao-paulo/"
    
    driver = initialise_driver(headless=False)
    wait = WebDriverWait(driver, 20)
    
    try:
        logging.info("--- INICIANDO MODO DE DEPURAÇÃO v2 ---")
        driver.get(start_url)
        
        logging.info("Aguardando pop-ups...")
        handle_initial_popups(driver, wait)
        
        # Passo crucial: esperar que os anúncios sejam carregados
        ad_selector = "a[href*='/anuncio/']"
        logging.info(f"Aguardando os anúncios aparecerem na página (seletor: {ad_selector})...")
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ad_selector)))
            logging.info("✅ Anúncios encontrados na página.")
        except TimeoutException:
            logging.error("TIMEOUT: Os anúncios não carregaram a tempo.")

        # Salvar o HTML depois de esperar
        logging.info("Salvando o estado da página após o carregamento dos anúncios...")
        save_debug_html(driver)
        
        logging.info("O script de depuração terminou. Por favor, verifique o novo 'debug.html'.")

    except Exception as e:
        logging.critical(f"Um erro crítico ocorreu: {e}", exc_info=True)
        save_debug_html(driver)
    finally:
        driver.quit()
        logging.info("🏁 Depuração concluída.")

if __name__ == "__main__":
    main()
