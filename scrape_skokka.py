"""
Enhanced web scraper for Skokka listings.

This module scrapes Skokka pages with improved reliability:
- Handles modals, cookie prompts
- Avoids infinite pagination
- Robust element handling
- Adds anti-detection flags and rich debugging (HTML/screenshot)
- Implements lazy-load scrolling and stronger waits
"""

from __future__ import annotations

import csv
import time
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class Listing:
    title: str
    description: str
    link: str
    image_url: str
    image_alt: str

    def as_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "description": self.description,
            "link": self.link,
            "image_url": self.image_url,
            "image_alt": self.image_alt,
        }


def initialise_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    # Performance/compat flags
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1366,768")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=pt-BR")
    options.add_argument("--accept-lang=pt-BR")
    # Anti-detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "load-extension"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    # Headless control (para debug vamos usar visível)
    if headless:
        # Alguns sites bloqueiam headless; quando necessário, troque para modo visível.
        options.add_argument("--headless=new")
    # Reduzir logs do Chromium no console (não silencia logs do site)
    options.add_argument("--log-level=3")
    options.add_argument("--disable-logging")

    # Reduz verbosidade do Chromium e direciona logs do chromedriver
    try:
        import os
        os.makedirs("debug", exist_ok=True)
    except Exception:
        pass
    service = Service(ChromeDriverManager().install())
    try:
        service.log_path = "debug/chromedriver.log"
    except Exception:
        pass
    driver = webdriver.Chrome(service=service, options=options)

    # Remover navigator.webdriver via DevTools
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en-US', 'en']});
Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                """
            },
        )
    except Exception:
        pass

    return driver


def accept_prompts(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    # Tenta diversos elementos de consentimento/cookie/idade em possíveis idiomas/variantes
    selectors = [
        (By.ID, "accept-disclaimer"),
        (By.CSS_SELECTOR, "button#onetrust-accept-btn-handler"),
        (By.XPATH, "//button[contains(translate(., 'ACEITAR', 'aceitar'), 'aceitar')]"),
        (By.XPATH, "//button[contains(translate(., 'CONCORDO', 'concordo'), 'concordo')]"),
        (By.XPATH, "//button[contains(translate(., 'ACCEPT', 'accept'), 'accept')]"),
        (By.XPATH, "//button[contains(translate(., 'ALLOW', 'allow'), 'allow')]"),
        (By.XPATH, "//button[contains(., 'Aceitar todos os cookies')]"),
        (By.XPATH, "//button[contains(., 'Aceitar')]"),
        (By.XPATH, "//button[contains(., 'I accept')]"),
        (By.XPATH, "//button[contains(., 'I Agree')]"),
    ]
    # Aplica um deadline global curto para evitar ruído
    end_time = time.time() + 10.0
    for by, value in selectors:
        if time.time() > end_time:
            break
        try:
            btn = wait.until(EC.element_to_be_clickable((by, value)))
            btn.click()
            # aguarda overlay sumir rapidamente
            time.sleep(0.2)
        except (TimeoutException, WebDriverException):
            continue

    # Fecha overlays comuns (se existirem)
    overlay_selectors = [
        ".cookie-banner, .cookie-consent, .gdpr, .consent, .modal-backdrop.show",
        ".ot-sdk-container",
        ".fc-consent-root",
    ]
    for sel in overlay_selectors:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in elems:
                driver.execute_script("arguments[0].style.display='none';", e)
        except WebDriverException:
            pass


def extract_listings(driver: webdriver.Chrome, wait: WebDriverWait) -> List[Listing]:
    """
    Extrai anúncios especificamente no formato do Skokka:
    - âncora do anúncio: <a class="line-clamp ... no-underline" data-pck ... href*="/anuncio/">
    - descrição curta: <span> adjacente/irmão próximo com o resumo
    - imagem: <img class="v-lazy-image ..."> próxima ao anúncio, capturando src e alt
    Mantém fallbacks para pequenas variações.
    """
    def scroll_to_load(max_steps: int = 8, pause: float = 0.8) -> None:
        last_height = driver.execute_script("return document.body.scrollHeight")
        stable_steps = 0
        for _ in range(max_steps):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                stable_steps += 1
                if stable_steps >= 2:
                    break
            else:
                stable_steps = 0
            last_height = new_height

    anchor_selectors = [
        "a.line-clamp.no-underline[data-pck][href*='/anuncio/']",
        "a.line-clamp-3.no-underline[data-pck][href*='/anuncio/']",
        "a[data-pck][href*='/anuncio/']",
        "a[href*='/anuncio/'], a[href*='/ad/']",
    ]

    scroll_to_load()

    anchors = []
    for sel in anchor_selectors:
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, sel)))
            anchors = driver.find_elements(By.CSS_SELECTOR, sel)
            if anchors:
                break
        except TimeoutException:
            continue

    if not anchors:
        print("[warn] Nenhum anúncio encontrado nesta página (âncoras não localizadas).")
        return []

    print(f"  – {len(anchors)} âncoras de anúncios detectadas.")

    def get_adjacent_description(a_el) -> str:
        try:
            desc = driver.execute_script(
                """
const a = arguments[0];
function getTextSafe(el){return (el && el.textContent || '').trim();}
let n = a.nextSibling;
let steps = 0;
while(n && steps < 8){
  if(n.nodeType === Node.ELEMENT_NODE){
    if(n.tagName.toLowerCase() === 'span' && getTextSafe(n)) return getTextSafe(n);
    const sp = n.querySelector && n.querySelector('span');
    if(sp && getTextSafe(sp)) return getTextSafe(sp);
    const p = n.querySelector && n.querySelector('p');
    if(p && getTextSafe(p)) return getTextSafe(p);
  }
  n = n.nextSibling;
  steps++;
}
return '';
                """,
                a_el,
            )
            if isinstance(desc, str) and desc.strip():
                return desc.strip()
        except WebDriverException:
            pass

        try:
            parent = a_el.find_element(By.XPATH, "./ancestor::*[self::li or self::article or self::div][1]")
            for css in ["span", ".description, [class*='desc']", "p"]:
                try:
                    cand = parent.find_element(By.CSS_SELECTOR, css)
                    text = cand.text.strip()
                    if text:
                        return text
                except NoSuchElementException:
                    continue
        except NoSuchElementException:
            pass

        return ""

    def get_related_image(a_el) -> "tuple[str, str]":
        """
        Localiza a imagem do anúncio próximo à âncora.
        Retorna (src, alt). Considera lazy-load e data-src.
        """
        # 1) Dentro do ancestral curto
        try:
            parent = a_el.find_element(By.XPATH, "./ancestor::*[self::li or self::article or self::div][1]")
            # candidatos de seletor de imagem
            for css in ["img.v-lazy-image", "img[class*='lazy']", "img"]:
                imgs = parent.find_elements(By.CSS_SELECTOR, css)
                for img in imgs:
                    try:
                        src = img.get_attribute("src") or img.get_attribute("data-src") or img.get_attribute("data-lazy-src") or ""
                        alt = img.get_attribute("alt") or ""
                        if src:
                            return src, alt
                    except WebDriverException:
                        continue
        except NoSuchElementException:
            pass

        # 2) Irmãos próximos
        try:
            sib_src = driver.execute_script(
                """
const a = arguments[0];
let n = a.previousSibling, steps = 0;
while(n && steps < 8){
  if(n.nodeType === Node.ELEMENT_NODE){
    const img = n.querySelector && (n.querySelector('img.v-lazy-image') || n.querySelector('img'));
    if(img){
      const src = img.getAttribute('src') || img.getAttribute('data-src') || img.getAttribute('data-lazy-src') || '';
      const alt = img.getAttribute('alt') || '';
      if(src) return [src, alt];
    }
  }
  n = n.previousSibling;
  steps++;
}
n = a.nextSibling; steps = 0;
while(n && steps < 8){
  if(n.nodeType === Node.ELEMENT_NODE){
    const img = n.querySelector && (n.querySelector('img.v-lazy-image') || n.querySelector('img'));
    if(img){
      const src = img.getAttribute('src') || img.getAttribute('data-src') || img.getAttribute('data-lazy-src') || '';
      const alt = img.getAttribute('alt') || '';
      if(src) return [src, alt];
    }
  }
  n = n.nextSibling;
  steps++;
}
return ['', ''];
                """,
                a_el,
            )
            if isinstance(sib_src, list) and len(sib_src) == 2:
                return sib_src[0] or "", sib_src[1] or ""
        except WebDriverException:
            pass

        return "", ""

    results: List[Listing] = []
    for a in anchors:
        try:
            title = (a.text or "").strip()
            link = a.get_attribute("href") or ""
            desc = get_adjacent_description(a)
            img_src, img_alt = get_related_image(a)

            if not title:
                for attr in ["title", "aria-label"]:
                    try:
                        val = a.get_attribute(attr)
                        if val and val.strip():
                            title = val.strip()
                            break
                    except WebDriverException:
                        continue

            if desc and title and desc.strip() == title.strip():
                desc = ""

            if title or link:
                results.append(Listing(
                    title=title,
                    description=desc,
                    link=link,
                    image_url=img_src,
                    image_alt=img_alt,
                ))
        except StaleElementReferenceException:
            continue
        except WebDriverException as e:
            print(f"[warn] Falha ao extrair um anúncio: {e}")
            continue

    return results


def go_to_next_page(driver: webdriver.Chrome, wait: WebDriverWait) -> bool:
    current_url = driver.current_url
    # 1) Botão clássico
    try:
        next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".pagination__next, a[rel='next']")))
        if not next_btn.is_enabled():
            return False
        href = next_btn.get_attribute("href")
        if href:
            driver.get(href)
        else:
            next_btn.click()
        # Espera mudança de URL ou presença de conteúdo-chave
        WebDriverWait(driver, 20).until(lambda d: d.current_url != current_url)
        return True
    except (TimeoutException, WebDriverException):
        pass

    # 2) Fallback: tentar construir próxima URL se houver ?page= N
    try:
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        url = driver.current_url
        pr = urlparse(url)
        qs = parse_qs(pr.query)
        page = int(qs.get("page", ["1"])[0])
        qs["page"] = [str(page + 1)]
        new_query = urlencode(qs, doseq=True)
        new_url = urlunparse((pr.scheme, pr.netloc, pr.path, pr.params, new_query, pr.fragment))
        if new_url != url:
            driver.get(new_url)
            WebDriverWait(driver, 20).until(lambda d: d.current_url != url)
            return True
    except Exception:
        pass

    return False


def write_to_csv(rows: List[Listing], filename: str = "skokka_listings.csv") -> None:
    headers = ["title", "description", "link", "image_url", "image_alt"]
    if not rows:
        print("[info] Nenhum anúncio para salvar.")
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        print(f"[info] 0 anúncios salvos em '{filename}'.")
        return

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows([r.as_dict() for r in rows])

    print(f"[info] {len(rows)} anúncios salvos em '{filename}'.")


def scrape_skokka(start_url: str, max_pages: Optional[int] = None, headless: bool = False) -> List[Listing]:
    """
    Durante a fase de diagnóstico, headless=False para visualizar o fluxo.
    """
    driver = initialise_driver(headless=headless)
    all_listings: List[Listing] = []

    def save_debug(prefix: str) -> None:
        import os
        os.makedirs("debug", exist_ok=True)
        try:
            with open(f"debug/{prefix}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except Exception:
            pass
        try:
            driver.save_screenshot(f"debug/{prefix}.png")
        except Exception:
            pass

    try:
        driver.get(start_url)
        wait = WebDriverWait(driver, 25)

        # Passo 1: aguarda carregamento completo do documento
        try:
            WebDriverWait(driver, 25).until(lambda d: d.execute_script("return document.readyState") == "complete")
        except TimeoutException:
            pass
        save_debug("page_1_loaded")

        accept_prompts(driver, wait)
        # Pequena espera apenas para transições de overlay
        time.sleep(0.5)
        save_debug("page_1_after_accept")

        page = 1
        while True:
            try:
                print(f"[info] Extraindo página {page}…")
                listings = extract_listings(driver, wait)
                if not listings:
                    # Salva debug adicional quando 0 anúncios
                    save_debug(f"page_{page}_zero_listings")
                else:
                    save_debug(f"page_{page}_ok")

                all_listings.extend(listings)

                if max_pages and page >= max_pages:
                    break
                if not go_to_next_page(driver, wait):
                    break

                page += 1
                # pequena pausa para evitar sobrecarga
                time.sleep(0.8)
            except Exception as e:
                print(f"[error] Falha ao processar página {page}: {e.__class__.__name__}: {e}")
                save_debug(f"page_{page}_error")
                break

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    return all_listings


def main() -> None:
    # Configura logging básico do nosso script
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s"
    )
    # Silencia ruído de libs verbosas (opcional)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("webdriver_manager").setLevel(logging.WARNING)

    start_url = "https://br.skokka.com/encontros/sao-paulo/"
    # Durante diagnóstico: headless=False e max_pages=1 para acelerar
    listings: List[Listing] = []
    try:
        # Removido o limite de páginas para coletar todas as páginas até não existir "próxima".
        # Para testes rápidos, você pode limitar: scrape_skokka(start_url, max_pages=2, headless=False)
        listings = scrape_skokka(start_url=start_url, headless=False)
    except Exception as e:
        print(f"[error] Falha geral na coleta: {e.__class__.__name__}: {e}")
    finally:
        write_to_csv(listings)
        print(f"[info] Coleta concluída: {len(listings)} anúncios (arquivo: skokka_listings.csv)")


if __name__ == "__main__":
    main()