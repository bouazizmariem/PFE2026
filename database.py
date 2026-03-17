import os
import json
from datetime import datetime
from pymongo import MongoClient
import certifi

# ============================
# CONFIG
# ============================

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://mariembouaziz:12345@cluster0.dlbfsmd.mongodb.net/..."
)
DB_NAME = "ecommerce_db"
COLLECTION_NAME = "products"


# ============================
# CONNEXION MONGODB
# ============================

def get_collection():
    """Crée la connexion uniquement quand on en a besoin."""
    client = MongoClient(
        MONGO_URI,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000   # timeout 10s
    )
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    collection.create_index("url", unique=True)
    return collection


# ============================
# INSERT / UPDATE PRODUIT
# ============================

def update_product(collection, product):

    url = product.get("url")
    if not url:
        return "skipped"

    new_price = product["price_history"][0]
    new_price["date"] = datetime.now().isoformat()

    existing = collection.find_one({"url": url})

    # ------------------------
    # PRODUIT EXISTE
    # ------------------------

    if existing:

        last_price = existing["price_history"][-1]

        changed = (
            last_price["price_final"] != new_price["price_final"]
            or last_price["availability"] != new_price["availability"]
        )

        new_price["changed"] = changed

        collection.update_one(
            {"url": url},
            {"$push": {"price_history": new_price}}
        )

        return "updated" if changed else "unchanged"

    # ------------------------
    # NOUVEAU PRODUIT
    # ------------------------

    new_price["changed"] = False
    collection.insert_one(product)

    return "inserted"


# ============================
# PIPELINE INGESTION
# ============================

def process_files():

    print("Connexion à MongoDB Atlas...")
    collection = get_collection()   # ← connexion ici, pas au démarrage
    print("Connexion MongoDB réussie ✅")

    total_inserted = 0
    total_updated = 0
    total_unchanged = 0
    total_skipped = 0

    if not os.path.exists(DATA_FOLDER):
        raise FileNotFoundError(f"Dossier introuvable : {DATA_FOLDER}")

    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".json")]

    if not files:
        print("Aucun fichier JSON trouvé dans", DATA_FOLDER)
        return

    for filename in files:

        file_path = os.path.join(DATA_FOLDER, filename)
        print(f"\n Traitement : {filename}")

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

            if status == "inserted":
                total_inserted += 1
            elif status == "updated":
                total_updated += 1
            elif status == "unchanged":
                total_unchanged += 1
            else:
                total_skipped += 1

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