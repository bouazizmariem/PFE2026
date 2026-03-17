import scrapy
import re
import time
from datetime import datetime


SCRAPED_DATE = datetime.now().strftime("%Y-%m-%d")


def clean_price(price):
    if not price:
        return None
    price = re.sub(r"[DT\u202f\s]", "", price).replace(",", ".")
    try:
        return float(price)
    except:
        return None


def subcategory_from_product_url(url: str) -> str:
    parts = url.rstrip("/").split("/")
    if len(parts) >= 2:
        slug = parts[-2]
        if slug and "spacenet" not in slug and "http" not in slug:
            return slug.replace("-", " ").title()
    return None


class SpacenetSpider(scrapy.Spider):
    name = "spacenet"

    MAIN_CATEGORY = "Electroménager"
    start_urls = ["https://www.tunisianet.com.tn/397-electromenager-tunisianet"]

    # ← custom_settings N'A PLUS de FEEDS (géré par run())
    custom_settings = {
        "CONCURRENT_REQUESTS": 64,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 64,
        "DOWNLOAD_DELAY": 0.1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.1,
        "AUTOTHROTTLE_MAX_DELAY": 3,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 32,
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429],
        "DOWNLOAD_TIMEOUT": 60,
        "LOG_LEVEL": "WARNING",
        
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._start_time = None
        self._product_count = 0

    def start_requests(self):
        self._start_time = time.perf_counter()
        self.logger.warning(f"🕐 Scraping démarré à {datetime.now().strftime('%H:%M:%S')}")
        yield from super().start_requests()

    def closed(self, reason):
        elapsed = time.perf_counter() - self._start_time
        minutes, seconds = divmod(int(elapsed), 60)
        self.logger.warning("=" * 50)
        self.logger.warning(f"✅ Scraping terminé — raison : {reason}")
        self.logger.warning(f"📦 Produits scrappés : {self._product_count}")
        self.logger.warning(f"⏱  Temps total       : {minutes}m {seconds}s ({elapsed:.2f}s)")
        if self._product_count:
            self.logger.warning(f"⚡ Vitesse moyenne   : {self._product_count / elapsed:.1f} produits/sec")
        self.logger.warning("=" * 50)

    def parse(self, response):
        for item in response.css("[data-id-product]"):
            url = item.css(".product_name a::attr(href)").get()
            if url:
                yield scrapy.Request(url, callback=self.parse_product)

        next_pages = response.css("ul.page-list a.js-search-link::attr(href)").getall()
        for href in next_pages:
            if "page=" in href:
                yield scrapy.Request(href, callback=self.parse)

    def parse_product(self, response):
        product_id = None
        match = re.search(r'/(\d+)-', response.url)
        if match:
            product_id = match.group(1)

        final_price   = clean_price(response.css(".current-price span::text").get())
        regular_price = clean_price(response.css(".regular-price::text").get())

        specs = {}
        keys   = response.css("dl.data-sheet dt.name::text").getall()
        values = response.css("dl.data-sheet dd::text").getall()
        for k, v in zip(keys, values):
            specs[k.strip()] = v.strip()

        subcategory = subcategory_from_product_url(response.url)

        self._product_count += 1

        yield {
            "id":             product_id,
            "name":           response.css("h1::text").get("").strip(),
            "reference":      response.css(".product-reference span::text").get("").strip(),
            "brand":          response.css(".product-manufacturer img::attr(alt)").get(),
            "category":       self.MAIN_CATEGORY,
            "subcategory":    subcategory,
            "price_final":    final_price,
            "price_original": regular_price,
            "availability":   response.css(
                ".label-available::text, .label-out-of-stock::text"
            ).get("Disponible").strip(),
            "description":    response.css(
                "#description, .product-description"
            ).xpath("string()").get("").strip(),
            "specifications": specs,
            "url":            response.url,
            "scraped_at":     SCRAPED_DATE,
        }




def run(output_file="data_raw/tunisianet_electroproducts.json"):
    import subprocess
    import sys
    import os

    spider_dir = os.path.dirname(os.path.abspath(__file__))

    result = subprocess.run(
        [
            sys.executable, "-m", "scrapy", "runspider",
            os.path.abspath(__file__),
            "-O", output_file,   # ✅ majuscule = overwrite, une seule option
            "-s", "LOG_LEVEL=WARNING",
        ],
        cwd=spider_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("STDERR:", result.stderr)
        raise Exception(f"Scrapy failed with code {result.returncode}")

    print(f"Scraping terminé → {output_file}")