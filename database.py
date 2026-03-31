import os
import json
from datetime import datetime
from pymongo import MongoClient
import certifi

# ============================
# CONFIG
# ============================

DB_NAME         = "ecommerce_db"
COLLECTION_NAME = "products"
DATA_FOLDER     = (
    os.environ.get("DATA_FOLDER")
    or os.path.join(os.path.dirname(__file__), "data_clean")
)


# ============================
# CONNEXION MONGODB
# ============================

def get_collection():
    uri = os.environ.get("MONGO_URI", "").strip()
    if not uri or not uri.startswith(("mongodb://", "mongodb+srv://")):
        raise ValueError(f"Invalid or missing MONGO_URI: {repr(uri)}")

    client = MongoClient(
        uri,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=20000,
        connectTimeoutMS=20000,
        socketTimeoutMS=20000,
    )
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    collection.create_index("url", unique=True)
    return client, collection


# ============================
# INSERT / UPDATE PRODUIT
# ============================

def update_product(collection, product):
    url = product.get("url")
    if not url:
        return "skipped"

    new_price = dict(product["price_history"][0])          # avoid mutating original
    new_price["ingested_at"] = datetime.now().isoformat()
    new_price.setdefault("date", new_price["ingested_at"]) # keep scraped date if present

    existing = collection.find_one({"url": url})

    if existing:
        last_price = existing["price_history"][-1]
        changed = (
            last_price.get("price_final")    != new_price.get("price_final")
            or last_price.get("availability") != new_price.get("availability")
        )
        new_price["changed"] = changed
        collection.update_one(
            {"url": url},
            {"$push": {"price_history": new_price}}
        )
        return "updated" if changed else "unchanged"

    new_price["changed"] = False
    collection.insert_one(product)
    return "inserted"


# ============================
# PIPELINE INGESTION
# ============================

def process_files():
    print("Connexion à MongoDB Atlas...")
    client = None

    try:
        client, collection = get_collection()
    except Exception as e:
        print(f"Erreur de connexion MongoDB : {e}")
        raise

    print("Connexion MongoDB réussie ✅")

    total_inserted  = 0
    total_updated   = 0
    total_unchanged = 0
    total_skipped   = 0

    try:
        if not os.path.exists(DATA_FOLDER):
            raise FileNotFoundError(f"Dossier introuvable : {DATA_FOLDER}")

        files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".json")]

        if not files:
            print("Aucun fichier JSON trouvé dans", DATA_FOLDER)
            return

        for filename in files:
            file_path = os.path.join(DATA_FOLDER, filename)
            print(f"\nTraitement : {filename}")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    products = json.load(f)
            except Exception as e:
                print(f"  Erreur lecture {filename} : {e}")
                continue

            for product in products:
                try:
                    status = update_product(collection, product)
                except Exception as e:
                    print(f"  Erreur produit {product.get('url', '?')} : {e}")
                    total_skipped += 1
                    continue

                if   status == "inserted":  total_inserted  += 1
                elif status == "updated":   total_updated   += 1
                elif status == "unchanged": total_unchanged += 1
                else:                       total_skipped   += 1

    finally:
        if client:
            client.close()

    print("\n==============================")
    print("Pipeline terminé")
    print("Produits insérés    :", total_inserted)
    print("Produits mis à jour :", total_updated)
    print("Produits inchangés  :", total_unchanged)
    print("Produits ignorés    :", total_skipped)
    print("==============================")


# ============================
# MAIN
# ============================

if __name__ == "__main__":
    process_files()