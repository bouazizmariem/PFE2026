import json
from datetime import datetime




def clean_description(desc):
    if not desc:
        return None
    desc = desc.replace("Lire la suite", "").replace("Lire moins", "").strip()
    if desc == "":
        return None
    return desc


def clean_brand(brand):
    if not brand or brand.lower() == "sans marque":
        return "Unknown"
    return brand


def clean_price(price):
    if price is None:
        return None
    return float(price)


def transform_product(product, site_name):     
    cleaned = {}
    cleaned["id"]          = product.get("id")
    cleaned["name"]        = product.get("name")
    cleaned["reference"]   = product.get("reference")
    cleaned["brand"]       = clean_brand(product.get("brand"))
    cleaned["category"]    = product.get("category")
    cleaned["subcategory"] = product.get("subcategory")
    cleaned["site"]        = site_name          

    availability = product.get("availability")

    cleaned["price_history"] = [
        {
            "date":           product.get("scraped_at"),
            "price_final":    clean_price(product.get("price_final")),
            "price_original": clean_price(product.get("price_original")),
            "availability":   availability
        }
    ]

    cleaned["description"]    = clean_description(product.get("description"))
    cleaned["specifications"] = product.get("specifications", {})
    cleaned["url"]            = product.get("url")

    return cleaned


def main(input_file, output_file, site_name):  

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned_data = [transform_product(p, site_name) for p in data]

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

    print(f"Cleaning {site_name} terminé ✅ → {output_file}")
    print("Produits nettoyés :", len(cleaned_data))


if __name__ == "__main__":
    # Spacenet
    main("data_raw/spacenet_electroproducts.json",          "data_clean/clean_spacenetElectroproducts.json",  "spacenet")
    main("data_raw/spacenet_infoproducts.json",      "data_clean/clean_spacenetInfoproducts.json",     "spacenet")
    # Tunisianet
    main("data_raw/tunisianet_Electroproducts.json", "data_clean/clean_TunisianetElectroproducts.json","tunisianet")
    main("data_raw/tunisianet_Infoproducts.json",    "data_clean/clean_TunisianetInfoproducts.json",   "tunisianet")