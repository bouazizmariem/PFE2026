import scrapy
import json
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_CATEGORY = "https://www.mytek.tn/informatique.html"
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
    slug = url.rstrip("/").split("/")[-1].replace(".html", "").split("?")[0]
    return slug.replace("-", " ").title()


# =========================
# VOLATILE API
# =========================

def fetch_volatile_batch(batch_ids):
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
            p["final_price"] = live.get("final_price", p.get("final_price"))
            p["price"]       = live.get("price",       p.get("price"))
            p["erpstock"]    = live.get("erpstock",    p.get("erpstock"))

    return products


# =========================
# SPIDER
# =========================

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
        "DEFAULT_REQUEST_HEADERS":         HEADERS,
        "ROBOTSTXT_OBEY":                  False,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._start_time = None
        self._products   = []
        self._seen_ids   = set()  # évite les doublons inter-pages

    async def start(self):
        self._start_time = time.perf_counter()
        self.logger.warning(f"Scraping démarré à {datetime.now().strftime('%H:%M:%S')}")
        for url in self.start_urls:
            yield scrapy.Request(url, headers=HEADERS)

    def closed(self, reason):
        elapsed = time.perf_counter() - self._start_time
        m, s    = divmod(int(elapsed), 60)
        self.logger.warning("=" * 50)
        self.logger.warning(f"Spider terminé — {reason}")
        self.logger.warning(f"Produits collectés : {len(self._products)}")
        self.logger.warning(f"Temps total        : {m}m {s}s")
        self.logger.warning("=" * 50)

    # ── 1. Page catégorie → sous-catégories ──────────────────────────

    def parse(self, response):
        self.logger.warning(f"STATUS: {response.status} | HTML: {len(response.text)} chars")

        subcat_links = set(
            href for href in response.css("ul.list-unstyled li a::attr(href)").getall()
            if href
            and "mytek.tn" in href
            and href != BASE_CATEGORY
            and href.endswith(".html")
            and "informatique" in href
        )

        self.logger.warning(f"{len(subcat_links)} sous-catégories trouvées")

        if subcat_links:
            for href in subcat_links:
                yield scrapy.Request(href, callback=self.parse_listing, headers=HEADERS)
        else:
            # Pas de sous-catégories → scraper la page directement
            yield from self.parse_listing(response)

    # ── 2. Page listing → data-attributes + pagination ───────────────

    def parse_listing(self, response):
        subcat_name = url_to_name(response.url)
        scraped_at  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cards     = response.css("[data-id]")
        new_count = 0

        for card in cards:
            g   = card.attrib.get
            pid = g("data-id", "").strip()

            if not pid or pid in self._seen_ids:
                continue

            self._seen_ids.add(pid)
            new_count += 1

            self._products.append({
                "id":           pid,
                "name":         g("data-name", "").strip(),
                "sku":          g("data-sku", "").strip(),
                "url":          g("data-url", "").strip(),
                "final_price":  g("data-final-price"),
                "price":        g("data-price"),
                "image":        g("data-image", "").strip(),
                "erpstock":     {"label": g("data-erpstock", "").strip()},
                "manufacturer": {"label": g("data-manufacturer", "").strip()},
                "description":  g("data-description", "").strip(),
                "category":     "Informatique",
                "subcategory":  subcat_name,
                "scraped_at":   scraped_at,
            })

        self.logger.warning(f"[{subcat_name}] {new_count} nouveaux produits")

        # ── Pagination : continue tant qu'on trouve des nouveaux produits
        if new_count > 0:
            import re
            current_page = int(re.search(r"[?&]p=(\d+)", response.url).group(1)) \
                if re.search(r"[?&]p=(\d+)", response.url) else 1
            base_url = response.url.split("?")[0]
            yield scrapy.Request(
                f"{base_url}?p={current_page + 1}",
                callback=self.parse_listing,
                headers=HEADERS,
                errback=lambda _: None,
            )


# =========================
# RUN
# =========================

def run(output_file="data_raw/mytek_infoproducts.json"):
    import os
    from scrapy.crawler import CrawlerProcess

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    all_products = []

    class CollectorSpider(MytekInfoSpider):
        def closed(self, reason):
            super().closed(reason)
            all_products.extend(self._products)

    print("Étape 1/2 — Collecte produits via Scrapy...")
    p = CrawlerProcess()
    p.crawl(CollectorSpider)
    p.start()

    if not all_products:
        print("❌ Aucun produit collecté")
        return

    print(f"  {len(all_products)} produits collectés")
    print("Étape 2/2 — Enrichissement via API volatile...")
    all_products = enrich_with_volatile(all_products)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=4)

    print(f"✅ Terminé → {output_file} ({len(all_products)} produits)")


if __name__ == "__main__":
    run()