# =========================================================
# DIAGNOSTIC CIBLÉ — Structure HTML listing Mytek
# Lance : python diagnose_mytek_listing.py
# =========================================================

import scrapy
from scrapy.crawler import CrawlerProcess

# URL directe d'une vraie sous-catégorie (pas une catégorie intermédiaire)
LISTING_URL = "https://www.mytek.tn/electromenager/lavage/machine-a-laver.html"


class DiagListing(scrapy.Spider):
    name        = "diag_listing"
    start_urls  = [LISTING_URL]
    custom_settings = {"LOG_LEVEL": "WARNING", "DOWNLOAD_TIMEOUT": 30}

    def parse(self, response):
        print("\n" + "=" * 60)
        print(f"URL    : {response.url}")
        print(f"Status : {response.status}")
        print("=" * 60)

        # ── 1. Chercher data-product-id (attribut clé de l'ancienne version) ──
        ids_attr = response.css("[data-product-id]::attr(data-product-id)").getall()
        print(f"\n[data-product-id]         → {len(ids_attr)} IDs : {ids_attr[:5]}")

        # ── 2. Chercher d'autres attributs data- sur les conteneurs ──────────
        containers = response.css("li.item, div.item, .product-item, article")
        print(f"\n[li.item / div.item / .product-item / article] → {len(containers)} éléments")
        for c in containers[:3]:
            print(f"  attrs : { {k: v for k, v in c.attrib.items()} }")

        # ── 3. Chercher tous les éléments avec des attributs data-* ──────────
        data_elements = response.xpath("//*[@*[starts-with(name(), 'data-')]]")
        print(f"\nÉléments avec data-* attrs : {len(data_elements)}")
        for el in data_elements[:10]:
            tag   = el.root.tag
            attrs = {k: v for k, v in el.attrib.items() if k.startswith("data-")}
            print(f"  <{tag}> {attrs}")

        # ── 4. Chercher les liens produits (URLs avec pattern numérique) ──────
        all_links = response.css("a::attr(href)").getall()
        product_links = [
            l for l in all_links
            if l and "mytek.tn" in l
            and l.endswith(".html")
            and any(c.isdigit() for c in l.split("/")[-1])   # URL produit contient des chiffres
        ]
        print(f"\nLiens avec chiffres dans le slug (URLs produits) → {len(product_links)}")
        for l in product_links[:5]:
            print(f"  {l}")

        # ── 5. Chercher scripts JSON (données produits injectées en JS) ───────
        scripts = response.css("script::text").getall()
        print(f"\nScripts JS : {len(scripts)}")
        for i, s in enumerate(scripts):
            if any(kw in s for kw in ["product", "price", "sku", "entity_id"]):
                print(f"\n  Script {i} (contient données produit) [{len(s)} chars] :")
                print(f"  {s[:500]}")

        # ── 6. Dump HTML complet pour inspecter la structure ─────────────────
        print("\n── HTML[:3000] ──────────────────────────────────────")
        print(response.text[:3000])

        # ── 7. Tester la pagination ──────────────────────────────────────────
        print("\n── Pagination ───────────────────────────────────────")
        pag_selectors = [
            "a[href*='?p=2']", "a[href*='page=2']",
            "a.next", "li.next a",
            ".toolbar-number", ".pages-item-next a",
            "a[title='Next']",
        ]
        for sel in pag_selectors:
            found = response.css(sel).get()
            print(f"  [{sel}] → {'TROUVÉ : ' + response.css(sel + '::attr(href)').get('') if found else 'non trouvé'}")


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(DiagListing)
    process.start()
