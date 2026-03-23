# =========================================================
# MYTEK ULTRA OPTIMIZED SCRAPER — ELECTROMENAGER
# =========================================================

import requests
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================================================
# CONFIGURATION
# =========================================================

BASE_CATEGORY = "https://www.mytek.tn/electromenager.html"
API_URL       = "https://www.mytek.tn/opensearch_api/api/productData"

HEADERS = {
    "User-Agent":       "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Accept":           "application/json"
}

BATCH_SIZE    = 40
MAX_WORKERS   = 5

MAIN_CATEGORY = BASE_CATEGORY.split("/")[-1].replace(".html", "").replace("-", " ").title()

# FIX : liste de sélecteurs candidats testés dans l'ordre
# Le premier qui retourne des liens internes Mytek est utilisé
SUBCATEGORY_SELECTORS = [
    "ul.list-unstyled li a",
    "ol.items li a",
    "ul.items li a",
    "div.block-content a",
    "div.sidebar a",
    "li.level1 a",
    "li.level2 a",
    "div.subcategories a",
    "div.categories-menu a",
    "div.category-description a",
    "nav a",
    "a[href*='/electromenager/']",   # fallback absolu : tous les liens de sous-cat
]


# =========================================================
# UTILITAIRE — Options Chrome compatibles Docker/CI Ubuntu
# =========================================================

def get_chrome_options():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")        # FIX CI : pas de GPU sur Ubuntu runner
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--ignore-certificate-errors")          # FIX CI : évite les erreurs SSL internes
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return options


def url_to_name(url: str) -> str:
    slug = url.split("/")[-1].replace(".html", "")
    return slug.replace("-", " ").title()


def is_valid_subcat_link(href: str) -> bool:
    """Vérifie qu'un lien est bien une sous-catégorie Mytek valide."""
    return (
        href
        and "mytek.tn" in href
        and href != BASE_CATEGORY
        and href.endswith(".html")
        and "electromenager" in href   # reste dans la bonne catégorie
    )


# =========================================================
# 1. RÉCUPÉRER SOUS-CATÉGORIES (Selenium)
# =========================================================

def get_subcategories(driver):
    print("Récupération sous-catégories...")

    driver.get(BASE_CATEGORY)

    # FIX CI : sleep + wait combinés — le sleep laisse le JS
    # s'initialiser avant que WebDriverWait commence à chercher
    time.sleep(3)

    # FIX : on attend que le body soit au moins chargé
    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except Exception as e:
        print(f"Page non chargée du tout : {e}")
        return []

    print(f"  Titre page : {driver.title}")
    print(f"  URL réelle : {driver.current_url}")

    # FIX : essai de chaque sélecteur dans l'ordre jusqu'à trouver des liens
    subcategories = []

    for selector in SUBCATEGORY_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            links = list(set([
                el.get_attribute("href")
                for el in elements
                if is_valid_subcat_link(el.get_attribute("href") or "")
            ]))

            if links:
                print(f"  Sélecteur retenu : '{selector}' → {len(links)} sous-catégories")
                subcategories = links
                break
            else:
                print(f"  '{selector}' → 0 liens, essai suivant...")

        except Exception as e:
            print(f"  '{selector}' → erreur : {e}")
            continue

    if not subcategories:
        # Dernier recours : dump HTML pour debug dans les logs CI
        print("\n  AUCUN sélecteur n'a fonctionné.")
        print(f"  HTML[:1000] :\n{driver.page_source[:1000]}")

    print(f"{len(subcategories)} sous-catégories trouvées")
    return subcategories


# =========================================================
# 2. RÉCUPÉRER TOUS LES IDS D'UNE CATÉGORIE
# =========================================================

def scrape_ids_from_category(driver, category_url):

    id_to_subcat     = {}
    page             = 1
    subcategory_name = url_to_name(category_url)
    seen_ids         = set()

    print(f"\n[{subcategory_name}] {category_url}")

    while True:

        url = f"{category_url}?p={page}"
        driver.get(url)

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-container"))
            )
        except:
            break   # page vide ou fin de pagination

        products = driver.find_elements(By.CSS_SELECTOR, "div.product-container")

        if not products:
            break

        page_ids = []

        for product in products:
            pid = product.get_attribute("data-product-id")
            if pid and pid not in seen_ids:
                page_ids.append(pid)
                seen_ids.add(pid)
                id_to_subcat[pid] = subcategory_name

        if not page_ids:
            break

        print(f"  Page {page} -> {len(page_ids)} produits")
        page += 1

    return id_to_subcat


# =========================================================
# 3. API BATCH (THREADING)
# =========================================================

def fetch_batch(batch_ids, id_to_subcat, scraped_at):

    ids_string = ",".join(batch_ids)
    url        = f"{API_URL}?ids={ids_string}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            products = list(data.values())
            for p in products:
                pid = str(p.get("id", ""))
                p["category"]    = MAIN_CATEGORY
                p["subcategory"] = id_to_subcat.get(pid, None)
                p["scraped_at"]  = scraped_at
            return products
        else:
            return []

    except Exception as e:
        print(f"Erreur API batch {batch_ids[:3]}... : {e}")
        return []


def fetch_all_products(id_to_subcat):

    print("\nRécupération détails via API (multi-thread)...")

    scraped_at   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    product_ids  = list(id_to_subcat.keys())
    all_products = []
    batches      = [product_ids[i:i+BATCH_SIZE] for i in range(0, len(product_ids), BATCH_SIZE)]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_batch, batch, id_to_subcat, scraped_at) for batch in batches]
        for i, future in enumerate(as_completed(futures), 1):
            data = future.result()
            all_products.extend(data)
            print(f"Batch {i}/{len(batches)} OK")

    print(f"\nTotal produits récupérés : {len(all_products)}")
    return all_products


# =========================================================
# 4. SAUVEGARDE JSON
# =========================================================

def save_to_json(products, output_file):

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    print(f"\nDonnées sauvegardées dans {output_file}")


# =========================================================
# PIPELINE PRINCIPAL
# =========================================================

def run(output_file="data_raw/mytek_Electroproducts.json"):

    start  = time.time()
    driver = webdriver.Chrome(options=get_chrome_options())

    try:
        subcategories = get_subcategories(driver)

        if not subcategories:
            print("Aucune sous-catégorie trouvée — scraping annulé.")
            return

        all_id_to_subcat = {}

        for sub in subcategories:
            id_map = scrape_ids_from_category(driver, sub)
            all_id_to_subcat.update(id_map)

    finally:
        driver.quit()

    print(f"\nTotal produits uniques : {len(all_id_to_subcat)}")

    if not all_id_to_subcat:
        print("Aucun produit trouvé — fichier JSON non créé.")
        return

    products = fetch_all_products(all_id_to_subcat)
    save_to_json(products, output_file)

    end = time.time()
    print(f"\nTemps total : {round(end - start, 2)} secondes")


if __name__ == "__main__":
    run()