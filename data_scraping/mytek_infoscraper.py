# =========================================================
# MYTEK ULTRA OPTIMIZED SCRAPER
# =========================================================

import requests
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


# =========================================================
# CONFIGURATION
# =========================================================

BASE_CATEGORY = "https://www.mytek.tn/informatique.html"
API_URL = "https://www.mytek.tn/opensearch_api/api/productData"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json"
}

BATCH_SIZE = 40
MAX_WORKERS = 5

MAIN_CATEGORY = BASE_CATEGORY.split("/")[-1].replace(".html", "").replace("-", " ").title()


# =========================================================
# UTILITAIRE — Options Chrome compatibles Docker
# =========================================================

def get_chrome_options():
    """Options Chrome obligatoires dans un conteneur Docker."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")              # obligatoire Docker
    options.add_argument("--disable-dev-shm-usage")   # obligatoire Docker
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return options


def url_to_name(url: str) -> str:
    slug = url.split("/")[-1].replace(".html", "")
    return slug.replace("-", " ").title()


# =========================================================
# 1. RÉCUPÉRER SOUS-CATÉGORIES (Selenium)
# =========================================================

def get_subcategories(driver):
    """Réutilise le driver existant — pas de nouveau driver ici."""

    print("Récupération sous-catégories...")

    driver.get(BASE_CATEGORY)
    time.sleep(0.8)

    elements = driver.find_elements(By.CSS_SELECTOR, "ul.list-unstyled li a")
    subcategories = list(set([
        el.get_attribute("href")
        for el in elements
        if el.get_attribute("href")
    ]))

    print(f"{len(subcategories)} sous-catégories trouvées")

    return subcategories


# =========================================================
# 2. RÉCUPÉRER TOUS LES IDS D'UNE CATÉGORIE
# =========================================================

def scrape_ids_from_category(driver, category_url):

    id_to_subcat = {}
    page = 1
    subcategory_name = url_to_name(category_url)

    print(f"\n[{subcategory_name}] {category_url}")

    while True:

        url = f"{category_url}?p={page}"
        driver.get(url)
        time.sleep(1)

        products = driver.find_elements(By.CSS_SELECTOR, "div.product-container")

        if not products:
            break

        page_ids = []

        for product in products:
            pid = product.get_attribute("data-product-id")
            if pid:
                page_ids.append(pid)
                id_to_subcat[pid] = subcategory_name

        if set(page_ids).issubset(set(id_to_subcat.keys())):
            break

        print(f"  Page {page} -> {len(page_ids)} produits")

        page += 1

    return id_to_subcat


# =========================================================
# 3. API BATCH (THREADING)
# =========================================================

def fetch_batch(batch_ids, id_to_subcat, scraped_at):

    ids_string = ",".join(batch_ids)
    url = f"{API_URL}?ids={ids_string}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
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
        print("Erreur API:", e)
        return []


def fetch_all_products(id_to_subcat):

    print("\nRécupération détails via API (multi-thread)...")

    scraped_at  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    product_ids = list(id_to_subcat.keys())
    all_products = []
    batches = [product_ids[i:i+BATCH_SIZE] for i in range(0, len(product_ids), BATCH_SIZE)]

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

def run(output_file="data_raw/mytek_infoproducts.json"):

    start = time.time()

    # Un seul driver créé ici, avec toutes les options Docker
    driver = webdriver.Chrome(options=get_chrome_options())

    try:
        # get_subcategories reçoit le driver — pas de second webdriver.Chrome()
        subcategories = get_subcategories(driver)

        all_id_to_subcat = {}

        for sub in subcategories:
            id_map = scrape_ids_from_category(driver, sub)
            all_id_to_subcat.update(id_map)

    finally:
        driver.quit()   # toujours fermé même si erreur

    print(f"\nTotal produits uniques : {len(all_id_to_subcat)}")

    products = fetch_all_products(all_id_to_subcat)

    save_to_json(products, output_file)

    end = time.time()
    print(f"\nTemps total : {round(end - start, 2)} secondes")


if __name__ == "__main__":
    run()