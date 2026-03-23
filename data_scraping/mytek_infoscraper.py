# =========================================================
# MYTEK ULTRA OPTIMIZED SCRAPER — INFORMATIQUE
# FIX CLOUDFLARE : cloudscraper remplace Selenium pour
# les requêtes HTTP bloquées par Cloudflare sur GitHub CI
# =========================================================

import json
import time
import cloudscraper
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================================================
# CONFIGURATION
# =========================================================

BASE_CATEGORY = "https://www.mytek.tn/informatique.html"
API_URL       = "https://www.mytek.tn/opensearch_api/api/productData"

BATCH_SIZE   = 40
MAX_WORKERS  = 5

MAIN_CATEGORY = BASE_CATEGORY.split("/")[-1].replace(".html", "").replace("-", " ").title()

# cloudscraper gère automatiquement les headers + challenge Cloudflare
scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "linux", "mobile": False}
)


# =========================================================
# UTILITAIRE — Options Chrome (pour scraper les produits)
# =========================================================

def get_chrome_options():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--ignore-certificate-errors")
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


# =========================================================
# 1. RÉCUPÉRER SOUS-CATÉGORIES — via cloudscraper + BeautifulSoup
# =========================================================

def get_subcategories():
    print("Récupération sous-catégories via cloudscraper...")

    try:
        response = scraper.get(BASE_CATEGORY, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Erreur requête cloudscraper : {e}")
        return []

    print(f"  Status HTTP : {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    selectors = [
        ("ul.list-unstyled li a",   lambda s: s.select("ul.list-unstyled li a")),
        ("ol.items li a",           lambda s: s.select("ol.items li a")),
        ("ul.items li a",           lambda s: s.select("ul.items li a")),
        ("div.block-content a",     lambda s: s.select("div.block-content a")),
        ("div.sidebar a",           lambda s: s.select("div.sidebar a")),
        ("li.level1 a",             lambda s: s.select("li.level1 a")),
        ("li.level2 a",             lambda s: s.select("li.level2 a")),
        ("nav a",                   lambda s: s.select("nav a")),
        # Fallback absolu
        ("a[href*=informatique]",   lambda s: s.find_all("a", href=lambda h: h and "/informatique/" in h)),
    ]

    subcategories = []

    for name, fn in selectors:
        elements = fn(soup)
        links = list(set([
            el.get("href")
            for el in elements
            if el.get("href")
            and "mytek.tn" in el.get("href")
            and el.get("href") != BASE_CATEGORY
            and el.get("href").endswith(".html")
            and "informatique" in el.get("href")
        ]))

        if links:
            print(f"  Sélecteur retenu : '{name}' → {len(links)} sous-catégories")
            subcategories = links
            break
        else:
            print(f"  '{name}' → 0 liens, essai suivant...")

    if not subcategories:
        print("  AUCUN sélecteur n'a fonctionné.")
        print(f"  HTML[:800] :\n{response.text[:800]}")

    print(f"{len(subcategories)} sous-catégories trouvées")
    return subcategories


# =========================================================
# 2. RÉCUPÉRER IDS PRODUITS — via Selenium
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
            break

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
# 3. API BATCH — via cloudscraper
# =========================================================

def fetch_batch(batch_ids, id_to_subcat, scraped_at):

    ids_string = ",".join(batch_ids)
    url        = f"{API_URL}?ids={ids_string}"

    try:
        response = scraper.get(url, timeout=15)
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

def run(output_file="data_raw/mytek_infoproducts.json"):

    start = time.time()

    # 1. Sous-catégories via cloudscraper (pas de Selenium ici)
    subcategories = get_subcategories()

    if not subcategories:
        print("Aucune sous-catégorie trouvée — scraping annulé.")
        return

    # 2. IDs produits via Selenium (une seule instance)
    driver = webdriver.Chrome(options=get_chrome_options())
    all_id_to_subcat = {}

    try:
        for sub in subcategories:
            id_map = scrape_ids_from_category(driver, sub)
            all_id_to_subcat.update(id_map)
    finally:
        driver.quit()

    print(f"\nTotal produits uniques : {len(all_id_to_subcat)}")

    if not all_id_to_subcat:
        print("Aucun produit trouvé — fichier JSON non créé.")
        return

    # 3. Détails via API (cloudscraper)
    products = fetch_all_products(all_id_to_subcat)
    save_to_json(products, output_file)

    end = time.time()
    print(f"\nTemps total : {round(end - start, 2)} secondes")


if __name__ == "__main__":
    run()