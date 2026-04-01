import os
import json
from datetime import datetime
from pymongo import MongoClient, UpdateOne
from pymongo.errors import AutoReconnect, NetworkTimeout, BulkWriteError
import certifi
import time

# ============================
# CONFIG
# ============================

DB_NAME         = "ecommerce_db"
COLLECTION_NAME = "products"
DATA_FOLDER     = (
    os.environ.get("DATA_FOLDER")
    or os.path.join(os.path.dirname(__file__), "data_clean")
)
BATCH_SIZE = 100  # nombre de produits par batch


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
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=60000,   # augmenté pour les bulk writes
        retryWrites=True,        # retry automatique côté Atlas
        maxPoolSize=1,           # une seule connexion (runner léger)
    )
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    collection.create_index("url", unique=True)
    return client, collection


# ============================
# BUILD OPERATION (sans requête réseau)
# ============================

def build_operation(product):
    """Construit un UpdateOne sans toucher MongoDB."""
    url = product.get("url")
    if not url:
        return None

    new_price = dict(product["price_history"][0])
    new_price["ingested_at"] = datetime.now().isoformat()
    new_price.setdefault("date", new_price["ingested_at"])
    new_price["changed"] = False  # Atlas pipeline peut pas le calculer ici

    return UpdateOne(
        {"url": url},
        {
            "$setOnInsert": {k: v for k, v in product.items() if k != "price_history"},
            "$push": {"price_history": new_price},
        },
        upsert=True
    )


# ============================
# BULK WRITE AVEC RETRY
# ============================

def bulk_write_with_retry(collection, operations, retries=3):
    for attempt in range(retries):
        try:
            result = collection.bulk_write(operations, ordered=False)
            return result
        except BulkWriteError as e:
            # erreurs partielles (ex: duplicates) → on continue
            print(f"  BulkWriteError (partiel) : {e.details.get('nInserted', 0)} insérés")
            return None
        except (AutoReconnect, NetworkTimeout) as e:
            wait = 2 ** attempt
            print(f"  Erreur réseau (tentative {attempt+1}/{retries}), retry dans {wait}s : {e}")
            time.sleep(wait)
    raise ConnectionError("Échec après plusieurs tentatives réseau")


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

    total_upserted = 0
    total_matched  = 0
    total_skipped  = 0

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

            # Découper en batches
            for i in range(0, len(products), BATCH_SIZE):
                batch = products[i:i + BATCH_SIZE]
                operations = []

                for product in batch:
                    op = build_operation(product)
                    if op:
                        operations.append(op)
                    else:
                        total_skipped += 1

                if not operations:
                    continue

                try:
                    result = bulk_write_with_retry(collection, operations)
                    if result:
                        total_upserted += result.upserted_count
                        total_matched  += result.matched_count
                        print(f"  Batch {i//BATCH_SIZE + 1} : "
                              f"{result.upserted_count} insérés, "
                              f"{result.matched_count} mis à jour")
                except Exception as e:
                    print(f"  Erreur batch {i//BATCH_SIZE + 1} : {e}")
                    total_skipped += len(operations)

    finally:
        if client:
            client.close()

    print("\n==============================")
    print("Pipeline terminé")
    print("Produits insérés/upserted :", total_upserted)
    print("Produits mis à jour        :", total_matched)
    print("Produits ignorés           :", total_skipped)
    print("==============================")


# ============================
# MAIN
# ============================

if __name__ == "__main__":
    process_files()