import json
import re
from datetime import datetime


# -----------------------------
# Nettoyer date
# -----------------------------
def clean_date(date_str):
    if not date_str:
        return None
    try:
        date_str = str(date_str).split(" ")[0]
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except:
        return None


# -----------------------------
# Normaliser disponibilité
# -----------------------------
def normalize_availability(status):
    if not status:
        return None

    status = status.strip()

    mapping = {
        "En stock":          "En stock",
        "Disponible":        "En stock",
        "Épuisé":            "Indisponible",
        "Epuisé":            "Indisponible",
        "Rupture de stock":  "Indisponible",
        "Indisponible":      "Indisponible",
        "Sur commande":      "Sur commande",
        "Sur commande 48h":  "Sur commande",
        "Sur Commande":      "Sur commande",
        "En Arrivage":       "En arrivage",
        "En arrivage":       "En arrivage",
    }

    return mapping.get(status, status)


# -----------------------------
# Nettoyer description
# -----------------------------
def clean_description(desc):
    if not desc:
        return None

    desc = re.sub("<.*?>", "", desc)
    desc = desc.replace("Lire la suite", "").replace("Lire moins", "")
    desc = desc.strip()

    if desc == "":
        return None

    return desc


# -----------------------------
# Nettoyer prix
# -----------------------------
def clean_price(price):
    if price is None:
        return None
    try:
        return float(price)
    except:
        return None


# -----------------------------
# Valider prix
# -----------------------------
def clean_prices(price_final, price_original):
    pf = clean_price(price_final)
    po = clean_price(price_original)

    # price_original invalide si <= price_final
    if po is not None and pf is not None and po <= pf:
        po = None

    # prix aberrant
    if pf is not None and pf < 10:
        pf = None

    return pf, po


# -----------------------------
# Nettoyer marque
# -----------------------------
def clean_brand(brand):
    if not brand or brand.strip() == "" or brand.lower() == "sans marque":
        return "Unknown"
    return brand.strip()


# -----------------------------
# Transformer produit
# -----------------------------
def transform_product(product, site_name):
    cleaned = {}

    cleaned["id"]          = str(product.get("id"))
    cleaned["name"]        = product.get("name")
    cleaned["reference"]   = product.get("reference")
    cleaned["brand"]       = clean_brand(product.get("brand"))
    cleaned["category"]    = product.get("category")
    cleaned["subcategory"] = product.get("subcategory")
    cleaned["site"]        = site_name

    # Date
    date = clean_date(product.get("scraped_at"))

    # Disponibilité
    availability = normalize_availability(product.get("availability"))

    # Prix
    price_final, price_original = clean_prices(
        product.get("price_final"),
        product.get("price_original")
    )

    cleaned["price_history"] = [
        {
            "date":           date,
            "price_final":    price_final,
            "price_original": price_original,
            "availability":   availability
        }
    ]

    cleaned["description"]    = clean_description(product.get("description"))
    cleaned["specifications"] = product.get("specifications", {})
    cleaned["url"]            = product.get("url")

    return cleaned


# -----------------------------
# MAIN
# -----------------------------
def main(input_file, output_file, site_name):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned_data = []
    skipped      = 0

    for product in data:
        cleaned = transform_product(product, site_name)

        # Ignore produits sans prix
        if cleaned["price_history"][0]["price_final"] is None:
            skipped += 1
            continue

        cleaned_data.append(cleaned)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

    print(f"Cleaning {site_name} terminé ✅ → {output_file}")
    print(f"Produits nettoyés : {len(cleaned_data)}")
    print(f"Produits ignorés  : {skipped}")


if __name__ == "__main__":
    # Spacenet
    main(
        "data_raw/spacenet_electroproducts.json",
        "data_clean/clean_spacenetElectroproducts.json",
        "spacenet"
    )
    main(
        "data_raw/spacenet_infoproducts.json",
        "data_clean/clean_spacenetInfoproducts.json",
        "spacenet"
    )
    # Tunisianet
    main(
        "data_raw/tunisianet_Electroproducts.json",
        "data_clean/clean_TunisianetElectroproducts.json",
        "tunisianet"
    )
    main(
        "data_raw/tunisianet_Infoproducts.json",
        "data_clean/clean_TunisianetInfoproducts.json",
        "tunisianet"
    )