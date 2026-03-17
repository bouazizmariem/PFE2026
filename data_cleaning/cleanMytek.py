import json
import re
from datetime import datetime





# -----------------------------
# Nettoyer description HTML
# -----------------------------
def clean_description(desc):

    if not desc:
        return None

    # supprimer balises HTML
    desc = re.sub("<.*?>", "", desc)

    # supprimer texte marketing
    desc = desc.split("Retrait en Magasin")[0]

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

    return float(price)


# -----------------------------
# Nettoyer disponibilité
# -----------------------------
def clean_availability(stock):

    if not stock:
        return None

    label = stock.get("label")

    if label:
        return label

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

        # corriger garantie
        if "garantie" in key.lower():
            value = clean_garantie(value)

        cleaned[key] = value

    return cleaned


# -----------------------------
# Transformer produit
# -----------------------------
def transform_product(product):

    cleaned = {}

    cleaned["id"] = str(product.get("id"))

    cleaned["name"] = product.get("name")

    cleaned["reference"] = product.get("sku")

    manufacturer = product.get("manufacturer")

    cleaned["brand"] = manufacturer.get("label") if manufacturer else None

    cleaned["category"] = product.get("category")

    cleaned["subcategory"] = product.get("subcategory")

    cleaned["site"] = "mytek"

    scraped = product.get("scraped_at")

    if scraped:
        date = scraped.split(" ")[0]
    else:
        date = None

    # récupérer disponibilité
    availability = clean_availability(product.get("erpstock"))

    # price history avec availability
    cleaned["price_history"] = [
        {
            "date": date,
            "price_final": clean_price(product.get("final_price")),
            "price_original": clean_price(product.get("price")),
            "availability": availability
        }
    ]

    description = clean_description(product.get("description"))

    cleaned["description"] = description

    specs = extract_specifications(description)

    cleaned["specifications"] = clean_specifications(specs)

    cleaned["url"] = product.get("url")

    return cleaned

# -----------------------------
# MAIN
# -----------------------------
def main(input_file, output_file):                 

    with open(input_file, "r", encoding="utf-8") as f:   
        data = json.load(f)

    cleaned_data = []

    for product in data:
        cleaned_product = transform_product(product)
        cleaned_data.append(cleaned_product)

    with open(output_file, "w", encoding="utf-8") as f:  
        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

    print(f"Cleaning Mytek terminé ✅ → {output_file}")
    print("Produits nettoyés :", len(cleaned_data))


if __name__ == "__main__":
    main(
        input_file="data_raw/mytek_Electroproducts.json",
        output_file="data_clean/clean_mytekElectproducts.json"
    )
    main(                                         
        input_file="data_raw/mytek_infoproducts.json",
        output_file="data_clean/clean_mytek_Infoproducts.json"
    )