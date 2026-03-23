# =========================================================
# MYTEK SPIDER — INFORMATIQUE
# Modèle identique à spacenetelecProd_spider.py :
#   parse()         → sous-catégories + pagination catégorie
#   parse_product() → détails produit via page produit
#   run()           → lance scrapy runspider en subprocess
# =========================================================

import scrapy
import re
import time
from datetime import datetime

SCRAPED_DATE  = datetime.now().strftime("%Y-%m-%d")
BASE_CATEGORY = "https://www.mytek.tn/informatique.html"


def clean_price(price_str):
    """Nettoie une chaîne de prix et retourne un float ou None."""
    if not price_str:
        return None
    cleaned = re.sub(r"[^\d,.]", "", price_str.strip()).replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def subcategory_from_url(url: str) -> str:
    """Extrait le nom de sous-catégorie depuis l'URL produit."""
    parts = url.rstrip("/").split("/")
    # URL pattern : .../informatique/sous-categorie/produit.html
    if len(parts) >= 3:
        slug = parts[-2]
        if slug and "mytek" not in slug and "http" not in slug:
            return slug.replace("-", " ").title()
    return None


# =========================================================
# SPIDER
# =========================================================

class MytekInfoSpider(scrapy.Spider):
    name = "mytek_info"

    MAIN_CATEGORY = "Informatique"
    start_urls    = [BASE_CATEGORY]

    custom_settings = {
        "CONCURRENT_REQUESTS":             16,
        "CONCURRENT_REQUESTS_PER_DOMAIN":  16,
        "DOWNLOAD_DELAY":                  0.3,
        "AUTOTHROTTLE_ENABLED":            True,
        "AUTOTHROTTLE_START_DELAY":        0.3,
        "AUTOTHROTTLE_MAX_DELAY":          5,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 8,
        "RETRY_TIMES":                     3,
        "RETRY_HTTP_CODES":                [500, 502, 503, 504, 408, 429],
        "DOWNLOAD_TIMEOUT":                60,
        "LOG_LEVEL":                       "WARNING",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._start_time    = None
        self._product_count = 0

    def start_requests(self):
        self._start_time = time.perf_counter()
        self.logger.warning(f"Scraping démarré à {datetime.now().strftime('%H:%M:%S')}")
        yield from super().start_requests()

    def closed(self, reason):
        elapsed = time.perf_counter() - self._start_time
        minutes, seconds = divmod(int(elapsed), 60)
        self.logger.warning("=" * 50)
        self.logger.warning(f"Spider terminé — raison : {reason}")
        self.logger.warning(f"Produits scrappés : {self._product_count}")
        self.logger.warning(f"Temps total       : {minutes}m {seconds}s ({elapsed:.2f}s)")
        if self._product_count:
            self.logger.warning(f"Vitesse moyenne   : {self._product_count / elapsed:.1f} produits/sec")
        self.logger.warning("=" * 50)

    # ── 1. Page principale → sous-catégories ─────────────────────────

    def parse(self, response):
        """
        Parse la page catégorie principale.
        Extrait les sous-catégories et les suit.
        Si aucune sous-cat trouvée, parse directement comme listing.
        """
        subcat_links = list(set([
            href for href in response.css("ul.list-unstyled li a::attr(href)").getall()
            if href
            and "mytek.tn" in href
            and href != BASE_CATEGORY
            and href.endswith(".html")
            and "informatique" in href
        ]))

        if subcat_links:
            self.logger.warning(f"{len(subcat_links)} sous-catégories trouvées")
            for href in subcat_links:
                yield scrapy.Request(href, callback=self.parse_listing)
        else:
            # Fallback : page principale traitée comme listing direct
            self.logger.warning("Aucune sous-catégorie — parsing direct de la page principale")
            yield from self.parse_listing(response)

    # ── 2. Page listing produits → liens produits + pagination ───────

    def parse_listing(self, response):
        """
        Parse une page de listing de produits.
        Suit chaque lien produit et pagine si nécessaire.
        """
        # Liens vers les pages produits individuelles
        product_links = response.css(
            "div.product-container a.product-name::attr(href), "
            "div.product-container h2 a::attr(href), "
            "li.item a.product-image::attr(href), "
            "a.product_name::attr(href)"
        ).getall()

        for href in set(product_links):
            if href and "mytek.tn" in href:
                yield scrapy.Request(href, callback=self.parse_product)

        # Pagination
        current_page = int(re.search(r"[?&]p=(\d+)", response.url).group(1)) \
            if re.search(r"[?&]p=(\d+)", response.url) else 1
        next_page    = current_page + 1
        base_url     = response.url.split("?")[0]

        has_next = response.css(
            f"a[href*='?p={next_page}'], a[href*='&p={next_page}']"
        ).get()

        if has_next and product_links:
            yield scrapy.Request(
                f"{base_url}?p={next_page}",
                callback=self.parse_listing
            )

    # ── 3. Page produit → données ────────────────────────────────────

    def parse_product(self, response):
        """Parse la page d'un produit individuel."""

        # Prix
        price_final    = clean_price(
            response.css(".price-box .price::text, .special-price .price::text").get()
        )
        price_original = clean_price(
            response.css(".old-price .price::text, .regular-price .price::text").get()
        )

        # Spécifications techniques
        specs = {}
        keys   = response.css("table.data-table th::text, dl.product-specs dt::text").getall()
        values = response.css("table.data-table td::text, dl.product-specs dd::text").getall()
        for k, v in zip(keys, values):
            k, v = k.strip(), v.strip()
            if k and v:
                specs[k] = v

        # Disponibilité
        availability = (
            response.css(".availability span::text, .stock-availability::text").get("")
        ).strip() or "Disponible"

        # Image
        image_url = response.css(
            "img#image-main::attr(src), "
            ".product-image img::attr(src), "
            "img.gallery-image::attr(src)"
        ).get()

        self._product_count += 1

        yield {
            "url":            response.url,
            "name":           response.css("h1.product-name::text, h1::text").get("").strip(),
            "reference":      response.css(
                ".product-reference::text, span[itemprop='sku']::text"
            ).get("").strip(),
            "brand":          response.css(
                ".product-manufacturer a::text, span[itemprop='brand']::text"
            ).get("").strip(),
            "category":       self.MAIN_CATEGORY,
            "subcategory":    subcategory_from_url(response.url),
            "price_history": [{
                "price_final":    price_final,
                "price_original": price_original,
                "availability":   availability,
                "date":           SCRAPED_DATE,
            }],
            "image_url":      image_url,
            "description":    response.css(
                "#description, .product-description"
            ).xpath("string()").get("").strip(),
            "specifications": specs,
            "scraped_at":     SCRAPED_DATE,
        }


# =========================================================
# RUN — identique au pattern spacenet
# =========================================================

def run(output_file="data_raw/mytek_infoproducts.json"):
    import subprocess
    import sys
    import os

    spider_dir = os.path.dirname(os.path.abspath(__file__))
    output_abs = os.path.abspath(output_file)
    os.makedirs(os.path.dirname(output_abs), exist_ok=True)

    result = subprocess.run(
        [
            sys.executable, "-m", "scrapy", "runspider",
            os.path.abspath(__file__),
            "-O", output_abs,
            "-s", "LOG_LEVEL=WARNING",
        ],
        cwd=spider_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("STDERR:", result.stderr[-2000:])
        raise Exception(f"Scrapy failed with code {result.returncode}")

    print(f"Scraping terminé → {output_abs}")


if __name__ == "__main__":
    run()