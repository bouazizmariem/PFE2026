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
# Nettoyer description HTML
# -----------------------------
def clean_description(desc):
    if not desc:
        return None

    desc = re.sub("<.*?>", "", desc)
    desc = desc.split("Retrait en Magasin")[0]
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
# Nettoyer disponibilité Mytek
# -----------------------------
def clean_availability(stock):
    if not stock:
        return None

    label = stock.get("label")

    if label:
        return normalize_availability(label)

    return None


# -----------------------------
# Corriger garantie
# -----------------------------
def clean_garantie(value):
    if not value:
        return value

    match = re.search(r"\d+\s*(ans|an|mois)", value.lower())

    if match:
        return match.group(0)

    return value


# -----------------------------
# Extraire specifications
# -----------------------------
def extract_specifications(description):
    if not description:
        return {}

    specs = {}
    description = description.replace("\n", " ")
    parts = description.split("-")

    for part in parts:
        part = part.strip()
        if ":" in part:
            key, value = part.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                specs[key] = value

    return specs


# -----------------------------
# Nettoyer specifications
# -----------------------------
def clean_specifications(specs):
    cleaned = {}

    for key, value in specs.items():
        key = key.strip()
        value = value.strip()

        if "garantie" in key.lower():
            value = clean_garantie(value)

        cleaned[key] = value

    return cleaned


# -----------------------------
# Transformer produit
# -----------------------------
def transform_product(product):
    cleaned = {}

    cleaned["id"]        = str(product.get("id"))
    cleaned["name"]      = product.get("name")
    cleaned["reference"] = product.get("sku")

    manufacturer     = product.get("manufacturer")
    cleaned["brand"] = clean_brand(
        manufacturer.get("label") if manufacturer else None
    )

    cleaned["category"]    = product.get("category")
    cleaned["subcategory"] = product.get("subcategory")
    cleaned["site"]        = "mytek"

    # Date
    date = clean_date(product.get("scraped_at"))

    # Disponibilité
    availability = clean_availability(product.get("erpstock"))

    # Prix
    price_final, price_original = clean_prices(
        product.get("final_price"),
        product.get("price")
    )

    cleaned["price_history"] = [
        {
            "date":           date,
            "price_final":    price_final,
            "price_original": price_original,
            "availability":   availability
        }
    ]

    description          = clean_description(product.get("description"))
    cleaned["description"]    = description
    specs                     = extract_specifications(description)
    cleaned["specifications"] = clean_specifications(specs)
    cleaned["url"]            = product.get("url")

    return cleaned


# -----------------------------
# MAIN
# -----------------------------
def main(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned_data = []
    skipped      = 0

    for product in data:
        cleaned = transform_product(product)

        # Ignore produits sans prix
        if cleaned["price_history"][0]["price_final"] is None:
            skipped += 1
            continue

        cleaned_data.append(cleaned)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

    print(f"Cleaning Mytek terminé ✅ → {output_file}")
    print(f"Produits nettoyés : {len(cleaned_data)}")
    print(f"Produits ignorés  : {skipped}")


if __name__ == "__main__":
    main(
        input_file="data_raw/mytek_Electroproducts.json",
        output_file="data_clean/clean_mytekElectproducts.json"
    )
    main(
        input_file="data_raw/mytek_infoproducts.json",
        output_file="data_clean/clean_mytek_Infoproducts.json"
    )