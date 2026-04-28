import scrapy
import json
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_CATEGORY = "https://www.mytek.tn/electromenager.html"
VOLATILE_API  = "https://www.mytek.tn/api/products/volatile"
BATCH_SIZE    = 48
MAX_WORKERS   = 5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.mytek.tn/",
}

API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.mytek.tn/",
}


def url_to_name(url: str) -> str:
    slug = url.rstrip("/").split("/")[-1].replace(".html", "")
    return slug.replace("-", " ").title()


# =========================
# VOLATILE API — prix live (optionnel)
# =========================

def fetch_volatile_batch(batch_ids):
    """Prix/stock live depuis l'API volatile (complète les data-attributes)."""
    try:
        r = requests.get(
            VOLATILE_API,
            params={"ids": ",".join(batch_ids)},
            headers=API_HEADERS,
            timeout=15
        )
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"  ❌ Volatile batch: {e}")
        return {}


def enrich_with_volatile(products):
    """Enrichit les produits avec les données live de l'API volatile."""
    ids     = [p["id"] for p in products]
    batches = [ids[i:i+BATCH_SIZE] for i in range(0, len(ids), BATCH_SIZE)]
    volatile_map = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(fetch_volatile_batch, b) for b in batches]
        for f in as_completed(futures):
            volatile_map.update(f.result())

    for p in products:
        live = volatile_map.get(str(p["id"]), {})
        if live:
            # Priorité aux données live pour prix et stock
            p["final_price"] = live.get("final_price", p.get("final_price"))
            p["price"]       = live.get("price",       p.get("price"))
            p["erpstock"]    = live.get("erpstock",    p.get("erpstock"))

    return products


# =========================
# SPIDER
# =========================

class MytekElecSpider(scrapy.Spider):
    name = "mytek_elec"
    start_urls = [BASE_CATEGORY]

    custom_settings = {
        "CONCURRENT_REQUESTS": 4,
        "DOWNLOAD_DELAY": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "RETRY_TIMES": 3,
        "DOWNLOAD_TIMEOUT": 60,
        "LOG_LEVEL": "WARNING",
        "DEFAULT_REQUEST_HEADERS": HEADERS,
        "ROBOTSTXT_OBEY": False,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._products = []

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(url, headers=HEADERS)

    def parse(self, response):
        self.logger.warning(f"STATUS: {response.status} | HTML: {len(response.text)} chars")

        links = set(
            href for href in response.css("ul.list-unstyled li a::attr(href)").getall()
            if href and "mytek.tn" in href and href.endswith(".html")
        )
        self.logger.warning(f"{len(links)} sous-catégories trouvées")

        for href in links:
            yield scrapy.Request(href, callback=self.parse_listing, headers=HEADERS)

    def parse_listing(self, response):
        subcat_name = url_to_name(response.url)
        scraped_at  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ── Extraction directe depuis les data-attributes ──
        cards = response.css("[data-id]")

        for card in cards:
            g = card.attrib.get  # raccourci

            pid = g("data-id", "").strip()
            if not pid:
                continue

            product = {
                "id":          pid,
                "name":        g("data-name", "").strip(),
                "sku":         g("data-sku", "").strip(),
                "url":         g("data-url", "").strip(),
                "final_price": g("data-final-price"),
                "price":       g("data-price"),
                "image":       g("data-image", "").strip(),
                "erpstock":    {"label": g("data-erpstock", "").strip()},
                "manufacturer": {"label": g("data-manufacturer", "").strip()},
                "description": g("data-description", "").strip(),
                "category":    "Electroménager",
                "subcategory": subcat_name,
                "scraped_at":  scraped_at,
            }
            self._products.append(product)

        # ── Pagination ──
        next_page = response.css("a.next::attr(href), a[rel='next']::attr(href)").get()
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse_listing, headers=HEADERS)
        else:
            self.logger.warning(f"[{subcat_name}] ✅ {len(cards)} produits")

    def closed(self, reason):
        self.logger.warning(f"Total produits scrapés : {len(self._products)}")


# =========================
# RUN
# =========================

def run(output_file="data_raw/mytek_Electroproducts.json"):
    import os
    from scrapy.crawler import CrawlerProcess

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    all_products = []

    class CollectorSpider(MytekElecSpider):
        def closed(self, reason):
            super().closed(reason)
            all_products.extend(self._products)

    p = CrawlerProcess()
    p.crawl(CollectorSpider)
    p.start()

    if not all_products:
        print("❌ Aucun produit collecté")
        return

    # Enrichissement optionnel avec prix live
    print("Enrichissement via API volatile...")
    all_products = enrich_with_volatile(all_products)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=4)

    print(f"✅ Terminé → {output_file} ({len(all_products)} produits)")


if __name__ == "__main__":
    run()