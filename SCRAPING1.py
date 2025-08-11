from __future__ import annotations

import csv
import time
from typing import Dict, List

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
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode
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
        except Exception as e:
            print(f"Erro ao aceitar o disclaimer: {e}")
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
    except Exception as e:
        print(f"Erro ao aceitar cookies: {e}")


def extract_listings(driver: webdriver.Chrome) -> List[Dict[str, str]]:
    """Extract image information from all listings on the current page."""
    data: List[Dict[str, str]] = []
    images = driver.find_elements(By.TAG_NAME, "img")
    for img in images:
        try:
            alt = img.get_attribute("alt") or ""
            # Removendo a verificação para "Encontros Casuais"
            src = img.get_attribute("src") or img.get_attribute("data-src") or ""
            if not src:
                continue
            data.append({"image_src": src, "image_alt": alt})
        except Exception as e:
            print(f"Erro ao extrair informações da imagem: {e}")
            continue
    return data


def go_to_next_page(driver: webdriver.Chrome, wait: WebDriverWait) -> bool:
    """Navigate to the next results page using the specified button."""
    try:
        next_button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "a.kiwii-btn.kiwii-btn-large.kiwii-display-inline-block")
            )
        )
        # Verifica se o texto do botão é "»"
        if next_button.text.strip() == "»":
            driver.execute_script("arguments[0].scrollIntoView();", next_button)
            next_button.click()
            wait.until(EC.staleness_of(next_button))
            return True
        return False
    except Exception as e:
        print(f"Erro ao navegar para a próxima página: {e}")
        return False


def write_to_csv(rows: List[Dict[str, str]], filename: str = "vivalocal_images.csv") -> None:
    """Write a list of dictionaries to CSV with headers."""
    if not rows:
        print("Nenhuma imagem encontrada, nenhum dado será salvo.")
        return
    fieldnames = list(rows[0].keys())
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Arquivo {filename} salvo com sucesso.")
    except Exception as e:
        print(f"Erro ao escrever no arquivo CSV: {e}")


def main() -> None:
    start_url = (
        "https://search.vivalocal.com/encontro-casual/sao-paulo/g?lb=new&search=1"
        "&start_field=1&select-this=132&searchGeoId=138&offer_type=offer&end_field="
    )
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
            print(f"  {len(rows)} imagens encontradas nesta página.")
            if not go_to_next_page(driver, wait):
                break
            page_counter += 1
            time.sleep(2)  # Delay para ser educado com o servidor
        write_to_csv(all_rows)
        print(f"Coleta concluída. {len(all_rows)} entradas salvas em 'vivalocal_images.csv'.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
