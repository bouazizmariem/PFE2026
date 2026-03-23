# =========================================================
# MYTEK SPIDER — INFORMATIQUE
# Stratégie :
#   1. parse()          → sous-catégories via ul.list-unstyled li a
#   2. parse_listing()  → extrait INITIAL_PRODUCTS_DATA du script JS
#                         + pagination incrémentale
#   3. fetch via API    → détails produits via opensearch_api
# =========================================================

import scrapy
import re
import json
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRAPED_DATE  = datetime.now().strftime("%Y-%m-%d")
BASE_CATEGORY = "https://www.mytek.tn/informatique.html"
API_URL       = "https://www.mytek.tn/opensearch_api/api/productData"
BATCH_SIZE    = 40
MAX_WORKERS   = 5

API_HEADERS = {
    "User-Agent":       "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Accept":           "application/json",
}


def url_to_name(url: str) -> str:
    parts = url.rstrip("/").split("/")
    if len(parts) >= 2:
        slug = parts[-1].replace(".html", "")
        return slug.replace("-", " ").title()
    return "Inconnu"


# =========================================================
# API BATCH
# =========================================================

def fetch_batch(batch_ids, id_to_subcat, scraped_at):
    try:
        response = requests.get(
            f"{API_URL}?ids={','.join(batch_ids)}",
            headers=API_HEADERS,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            products = list(data.values())
            for p in products:
                pid = str(p.get("id", ""))
                p["category"]    = "Informatique"
                p["subcategory"] = id_to_subcat.get(pid)
                p["scraped_at"]  = scraped_at
            return products

    except Exception as e:
        print(f"Erreur API batch {batch_ids[:3]}... : {e}")

    return []


def fetch_all_products(id_to_subcat):
    print(f"\nFetch API pour {len(id_to_subcat)} produits...")
    scraped_at   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    product_ids  = list(id_to_subcat.keys())
    all_products = []
    batches      = [product_ids[i:i+BATCH_SIZE] for i in range(0, len(product_ids), BATCH_SIZE)]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_batch, batch, id_to_subcat, scraped_at) for batch in batches]
        for i, future in enumerate(as_completed(futures), 1):
            all_products.extend(future.result())
            print(f"  Batch {i}/{len(batches)} OK")

    print(f"Total produits récupérés : {len(all_products)}")
    return all_products


# =========================================================
# SPIDER
# =========================================================

class MytekInfoSpider(scrapy.Spider):
    name       = "mytek_info"
    start_urls = [BASE_CATEGORY]

    custom_settings = {
        "CONCURRENT_REQUESTS":             8,
        "CONCURRENT_REQUESTS_PER_DOMAIN":  8,
        "DOWNLOAD_DELAY":                  0.5,
        "AUTOTHROTTLE_ENABLED":            True,
        "AUTOTHROTTLE_START_DELAY":        0.5,
        "AUTOTHROTTLE_MAX_DELAY":          5,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 4,
        "RETRY_TIMES":                     3,
        "RETRY_HTTP_CODES":                [500, 502, 503, 504, 408, 429],
        "DOWNLOAD_TIMEOUT":                60,
        "LOG_LEVEL":                       "WARNING",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._start_time   = None
        self._id_to_subcat = {}

    def start_requests(self):
        self._start_time = time.perf_counter()
        self.logger.warning(f"Scraping démarré à {datetime.now().strftime('%H:%M:%S')}")
        yield from super().start_requests()

    def closed(self, reason):
        elapsed = time.perf_counter() - self._start_time
        m, s    = divmod(int(elapsed), 60)
        self.logger.warning("=" * 50)
        self.logger.warning(f"Spider terminé — {reason}")
        self.logger.warning(f"IDs collectés : {len(self._id_to_subcat)}")
        self.logger.warning(f"Temps total   : {m}m {s}s")
        self.logger.warning("=" * 50)

    # ── 1. Page catégorie principale → sous-catégories ───────────────

    def parse(self, response):
        subcat_links = list(set([
            href for href in response.css("ul.list-unstyled li a::attr(href)").getall()
            if href
            and "mytek.tn" in href
            and href != BASE_CATEGORY
            and href.endswith(".html")
            and "informatique" in href
        ]))

        self.logger.warning(f"{len(subcat_links)} sous-catégories trouvées")

        if subcat_links:
            for href in subcat_links:
                yield scrapy.Request(href, callback=self.parse_listing)
        else:
            yield from self.parse_listing(response)

    # ── 2. Page listing → INITIAL_PRODUCTS_DATA + pagination ─────────

    def parse_listing(self, response):
        subcategory_name = url_to_name(response.url.split("?")[0])

        ids_found = 0
        for script in response.css("script::text").getall():
            if "INITIAL_PRODUCTS_DATA" in script:
                match = re.search(r"INITIAL_PRODUCTS_DATA\s*=\s*(\[.*?\]);", script, re.DOTALL)
                if match:
                    try:
                        products_data = json.loads(match.group(1))
                        for item in products_data:
                            pid = str(item.get("id", ""))
                            if pid and pid not in self._id_to_subcat:
                                self._id_to_subcat[pid] = subcategory_name
                                ids_found += 1
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"JSON parse error sur {response.url} : {e}")
                break

        if ids_found:
            self.logger.warning(f"  [{subcategory_name}] {ids_found} IDs extraits")
        else:
            self.logger.warning(f"  [{subcategory_name}] INITIAL_PRODUCTS_DATA non trouvé")

        # Pagination incrémentale
        current_page = int(re.search(r"[?&]p=(\d+)", response.url).group(1)) \
            if re.search(r"[?&]p=(\d+)", response.url) else 1

        if ids_found > 0:
            next_page = current_page + 1
            base_url  = response.url.split("?")[0]
            yield scrapy.Request(
                f"{base_url}?p={next_page}",
                callback=self.parse_listing,
                errback=self.handle_pagination_error,
            )

    def handle_pagination_error(self, failure):
        pass


# =========================================================
# RUN
# =========================================================

def run(output_file="data_raw/mytek_infoproducts.json"):
    import os
    from scrapy.crawler import CrawlerProcess

    output_abs = os.path.abspath(output_file)
    os.makedirs(os.path.dirname(output_abs), exist_ok=True)

    # ── Étape 1 : spider collecte les IDs ────────────────────────────
    print("Étape 1/2 — Collecte IDs via Scrapy...")

    id_to_subcat = {}

    class CollectorSpider(MytekInfoSpider):
        def closed(self, reason):
            super().closed(reason)
            id_to_subcat.update(self._id_to_subcat)

    process = CrawlerProcess({"LOG_LEVEL": "WARNING", "AUTOTHROTTLE_ENABLED": True})
    process.crawl(CollectorSpider)
    process.start()

    print(f"  {len(id_to_subcat)} IDs collectés")

    if not id_to_subcat:
        print("Aucun produit trouvé — fichier JSON non créé.")
        return

    # ── Étape 2 : fetch API ───────────────────────────────────────────
    print("Étape 2/2 — Fetch détails via API...")
    products = fetch_all_products(id_to_subcat)

    with open(output_abs, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    print(f"Scraping terminé → {output_abs} ({len(products)} produits)")


if __name__ == "__main__":
    run()