import scrapy
import re
import json
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRAPED_DATE  = datetime.now().strftime("%Y-%m-%d")
BASE_CATEGORY = "https://www.mytek.tn/electromenager.html"
API_URL       = "https://www.mytek.tn/opensearch_api/api/productData"
BATCH_SIZE    = 40
MAX_WORKERS   = 5

# 🔥 HEADERS navigateur (IMPORTANT pour GitHub Actions)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
}

API_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json",
}


def url_to_name(url: str) -> str:
    parts = url.rstrip("/").split("/")
    if len(parts) >= 1:
        slug = parts[-1].replace(".html", "")
        return slug.replace("-", " ").title()
    return "Inconnu"


# =========================
# API BATCH
# =========================

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
                p["category"]    = "Electroménager"
                p["subcategory"] = id_to_subcat.get(pid)
                p["scraped_at"]  = scraped_at
            return products

    except Exception as e:
        print(f"Erreur API batch : {e}")

    return []


def fetch_all_products(id_to_subcat):
    print(f"\nFetch API pour {len(id_to_subcat)} produits...")
    scraped_at   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    product_ids  = list(id_to_subcat.keys())
    all_products = []

    batches = [product_ids[i:i+BATCH_SIZE] for i in range(0, len(product_ids), BATCH_SIZE)]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_batch, batch, id_to_subcat, scraped_at) for batch in batches]
        for i, future in enumerate(as_completed(futures), 1):
            all_products.extend(future.result())
            print(f"Batch {i}/{len(batches)} OK")

    print(f"Total produits récupérés : {len(all_products)}")
    return all_products


# =========================
# SPIDER
# =========================

class MytekElecSpider(scrapy.Spider):
    name = "mytek_elec"
    start_urls = [BASE_CATEGORY]

    custom_settings = {
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 0.5,
        "AUTOTHROTTLE_ENABLED": True,
        "RETRY_TIMES": 3,
        "DOWNLOAD_TIMEOUT": 60,
        "LOG_LEVEL": "WARNING",

        # 🔥 FIX GitHub Actions
        "DEFAULT_REQUEST_HEADERS": HEADERS,
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "ROBOTSTXT_OBEY": False,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._start_time   = None
        self._id_to_subcat = {}

    def start_requests(self):
        self._start_time = time.perf_counter()
        self.logger.warning("Scraping démarré")

        for url in self.start_urls:
            yield scrapy.Request(url, headers=HEADERS)

    def parse(self, response):
        self.logger.warning(f"STATUS: {response.status} | HTML size: {len(response.text)}")

        subcat_links = list(set([
            href for href in response.css("ul.list-unstyled li a::attr(href)").getall()
            if href and "mytek.tn" in href and href.endswith(".html")
        ]))

        self.logger.warning(f"{len(subcat_links)} sous-catégories trouvées")

        for href in subcat_links:
            yield scrapy.Request(href, callback=self.parse_listing, headers=HEADERS)

    def parse_listing(self, response):
        subcategory_name = url_to_name(response.url)
        ids_found = 0

        for script in response.css("script::text").getall():
            if "INITIAL_PRODUCTS_DATA" in script:
                match = re.search(r"INITIAL_PRODUCTS_DATA\s*=\s*(\[.*?\]);", script, re.DOTALL)
                if match:
                    try:
                        products_data = json.loads(match.group(1))
                        for item in products_data:
                            pid = str(item.get("id", ""))
                            if pid:
                                self._id_to_subcat[pid] = subcategory_name
                                ids_found += 1
                    except:
                        pass
                break

        if ids_found:
            self.logger.warning(f"[{subcategory_name}] {ids_found} IDs")
        else:
            self.logger.warning(f"[{subcategory_name}] ❌ Aucun ID (probablement bloqué)")

    def closed(self, reason):
        elapsed = time.perf_counter() - self._start_time
        self.logger.warning(f"IDs collectés : {len(self._id_to_subcat)}")


# =========================
# RUN
# =========================

def run(output_file="data_raw/mytek_products.json"):
    import os
    from scrapy.crawler import CrawlerProcess

    output_abs = os.path.abspath(output_file)
    os.makedirs(os.path.dirname(output_abs), exist_ok=True)

    id_to_subcat = {}

    class CollectorSpider(MytekElecSpider):
        def closed(self, reason):
            super().closed(reason)
            id_to_subcat.update(self._id_to_subcat)

    process = CrawlerProcess()
    process.crawl(CollectorSpider)
    process.start()

    print(f"{len(id_to_subcat)} IDs collectés")

    if not id_to_subcat:
        print("❌ PROBLEME: aucun ID → site probablement bloqué")
        return

    products = fetch_all_products(id_to_subcat)

    with open(output_abs, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    print(f"Scraping terminé → {output_abs}")


if __name__ == "__main__":
    run()