# =========================================================
# DIAGNOSTIC — Trouver les vrais sélecteurs Mytek
# Lance : python diagnose_mytek_selectors.py
# =========================================================

import scrapy
from scrapy.crawler import CrawlerProcess

BASE_CATEGORY = "https://www.mytek.tn/electromenager.html"


class DiagSpider(scrapy.Spider):
    name = "diag"
    start_urls = [BASE_CATEGORY]

    custom_settings = {
        "LOG_LEVEL": "WARNING",
        "DOWNLOAD_TIMEOUT": 30,
    }

    def parse(self, response):
        print("\n" + "=" * 60)
        print("PAGE CATÉGORIE PRINCIPALE")
        print(f"URL   : {response.url}")
        print(f"Status: {response.status}")
        print("=" * 60)

        # ── Tester sélecteurs sous-catégories ────────────────
        subcat_selectors = [
            "ul.list-unstyled li a",
            "ol.items li a",
            "ul.items li a",
            "div.block-content a",
            "div.sidebar a",
            "li.level1 a",
            "li.level2 a",
            "nav a",
            "a[href*='/electromenager/']",
        ]

        print("\n── Sélecteurs SOUS-CATÉGORIES ──────────────────────")
        best_subcat = None
        for sel in subcat_selectors:
            links = [
                h for h in response.css(f"{sel}::attr(href)").getall()
                if h and "mytek.tn" in h and "electromenager" in h and h.endswith(".html")
            ]
            print(f"  [{sel}] → {len(links)} liens")
            for l in links[:3]:
                print(f"      {l}")
            if links and best_subcat is None:
                best_subcat = (sel, links[0])

        # ── Dump HTML brut (500 chars) ────────────────────────
        print("\n── HTML[:1000] ──────────────────────────────────────")
        print(response.text[:1000])

        # ── Suivre le premier lien produit trouvé ────────────
        if best_subcat:
            print(f"\nSuivi sous-catégorie : {best_subcat[1]}")
            yield scrapy.Request(best_subcat[1], callback=self.parse_subcat)
        else:
            print("\nAucune sous-catégorie trouvée — test de la page principale comme listing")
            yield scrapy.Request(response.url, callback=self.parse_subcat, dont_filter=True)

    def parse_subcat(self, response):
        print("\n" + "=" * 60)
        print("PAGE SOUS-CATÉGORIE / LISTING")
        print(f"URL   : {response.url}")
        print("=" * 60)

        # ── Tester sélecteurs liens produits ─────────────────
        product_link_selectors = [
            "div.product-container a.product-name",
            "div.product-container h2 a",
            "li.item a.product-image",
            "a.product_name",
            "div.product-container a",
            ".products-grid li a",
            "h2.product-name a",
            "a[href*='/electromenager/'][href$='.html']",
        ]

        print("\n── Sélecteurs LIENS PRODUITS ────────────────────────")
        best_product = None
        for sel in product_link_selectors:
            links = [
                h for h in response.css(f"{sel}::attr(href)").getall()
                if h and "mytek.tn" in h
            ]
            print(f"  [{sel}] → {len(links)} liens")
            for l in links[:2]:
                print(f"      {l}")
            if links and best_product is None:
                best_product = links[0]

        # ── Sélecteurs pagination ─────────────────────────────
        print("\n── Sélecteurs PAGINATION ───────────────────────────")
        pagination_selectors = [
            "a[href*='?p=2']",
            "a.next",
            "li.next a",
            ".pages a",
            "ul.page-list a",
        ]
        for sel in pagination_selectors:
            found = response.css(sel).get()
            print(f"  [{sel}] → {'TROUVÉ' if found else 'non trouvé'}")

        # ── HTML listing ──────────────────────────────────────
        print("\n── HTML[:1000] ──────────────────────────────────────")
        print(response.text[:1000])

        # ── Suivre le premier lien produit ────────────────────
        if best_product:
            print(f"\nSuivi produit : {best_product}")
            yield scrapy.Request(best_product, callback=self.parse_product)

    def parse_product(self, response):
        print("\n" + "=" * 60)
        print("PAGE PRODUIT")
        print(f"URL   : {response.url}")
        print("=" * 60)

        # ── Tester sélecteurs produit ─────────────────────────
        tests = {
            "Nom (h1)"          : response.css("h1::text").getall(),
            "Nom (.product-name)": response.css("h1.product-name::text").getall(),
            "Prix (.price)"     : response.css(".price::text").getall(),
            "Prix (.price-box)" : response.css(".price-box .price::text").getall(),
            "Prix (special)"    : response.css(".special-price .price::text").getall(),
            "Prix (old)"        : response.css(".old-price .price::text").getall(),
            "Dispo (.availability)": response.css(".availability span::text").getall(),
            "Dispo (.stock)"    : response.css(".stock-availability::text").getall(),
            "Ref (.product-ref)": response.css(".product-reference::text").getall(),
            "Ref (sku)"         : response.css("span[itemprop='sku']::text").getall(),
            "Marque (.manufacturer)": response.css(".product-manufacturer a::text").getall(),
            "Specs (table th)"  : response.css("table.data-table th::text").getall()[:5],
            "Specs (dl dt)"     : response.css("dl.product-specs dt::text").getall()[:5],
            "Image (img#image-main)": response.css("img#image-main::attr(src)").getall(),
            "Image (.product-image img)": response.css(".product-image img::attr(src)").getall(),
        }

        print("\n── Résultats sélecteurs PRODUIT ────────────────────")
        for label, values in tests.items():
            status = "✅" if values else "❌"
            print(f"  {status} {label}: {values[:2] if values else 'RIEN'}")

        print("\n── HTML[:2000] ──────────────────────────────────────")
        print(response.text[:2000])


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(DiagSpider)
    process.start()
