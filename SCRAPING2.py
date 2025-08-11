from __future__ import annotations

import csv
import time
from typing import Dict, List
from selenium.common.exceptions import TimeoutException  # Importando a exceção TimeoutException

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def initialise_driver() -> webdriver.Chrome:
    """Configure and return a new Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")  # Colocamos o headless para evitar a janela pop-up
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation", "load-extension"]
    )
    chrome_options.add_experimental_option("useAutomationExtension", False)
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def accept_prompts(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    """Accept disclaimer and cookie prompts if they appear."""
    for _ in range(2):
        try:
            button = wait.until(
                EC.element_to_be_clickable((By.ID, "accept-disclaimer"))
            )
            button.click()
        except Exception:
            break
    try:
        cookie_button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(translate(., 'ACEITAR', 'aceitar'), 'aceitar todos os cookies') "
                    "or contains(translate(., 'ACCEPT', 'accept'), 'accept all cookies')]",
                )
            )
        )
        cookie_button.click()
    except Exception:
        pass


def extract_listings(driver: webdriver.Chrome) -> List[Dict[str, str]]:
    """Extract information from all listings on the current page."""
    data: List[Dict[str, str]] = []
    
    # Aguarde explicitamente até que os anúncios estejam visíveis
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".offer__item"))
        )
    except TimeoutException:
        print("Erro: Não foi possível encontrar os anúncios. Verifique a estrutura da página.")
        return data  # Retorna lista vazia caso os anúncios não sejam encontrados

    listings = driver.find_elements(By.CSS_SELECTOR, ".offer__item")
    print(f"Anúncios encontrados: {len(listings)}")  # Log para verificar a quantidade de anúncios encontrados

    for listing in listings:
        try:
            title = listing.find_element(By.CSS_SELECTOR, ".offer__title").text
            description = listing.find_element(By.CSS_SELECTOR, ".offer__description").text
            link = listing.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            data.append({"title": title, "description": description, "link": link})
        except Exception as e:
            print(f"Erro ao extrair o anúncio: {e}")
            continue
    return data


def go_to_next_page(driver: webdriver.Chrome, wait: WebDriverWait) -> bool:
    """Navigate to the next results page using the specified button."""
    try:
        next_button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".pagination__next")
            )
        )
        if next_button.is_enabled():
            next_button.click()
            wait.until(EC.staleness_of(next_button))
            return True
        return False
    except Exception:
        return False


def write_to_csv(rows: List[Dict[str, str]], filename: str = "skokka_listings.csv") -> None:
    """Write a list of dictionaries to CSV with headers."""
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    start_url = "https://br.skokka.com/encontros/sao-paulo/"
    driver = initialise_driver()
    all_rows: List[Dict[str, str]] = []
    try:
        driver.get(start_url)
        wait = WebDriverWait(driver, 20)
        accept_prompts(driver, wait)
        page_counter = 1
        while True:
            print(f"Extraindo página {page_counter}…")
            rows = extract_listings(driver)
            all_rows.extend(rows)
            print(f"  {len(rows)} anúncios encontrados nesta página.")
            if not go_to_next_page(driver, wait):
                break
            page_counter += 1
            time.sleep(3)  # Aumentar o tempo de espera para garantir o carregamento da página
        write_to_csv(all_rows)
        print(f"Coleta concluída. {len(all_rows)} entradas salvas em 'skokka_listings.csv'.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
