import os
from pymongo import MongoClient
import certifi

# ============================
# CONFIG
# ============================
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    MONGO_URI = input("Entre ton MONGO_URI : ").strip()

client = MongoClient(
    MONGO_URI,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=20000,
)
collection = client["ecommerce_db"]["products"]

# ============================
# FIX
# ============================
print("Connexion MongoDB réussie ✅")
print("Correction des price_original invalides...")

fixed    = 0
checked  = 0

for product in collection.find(
    { "price_history.price_original": { "$ne": None } },
    { "price_history": 1 }
):
    checked += 1
    new_history = []
    changed = False

    for entry in product["price_history"]:
        po = entry.get("price_original")
        pf = entry.get("price_final")

        if po is not None and pf is not None and po <= pf:
            entry["price_original"] = None
            changed = True

        new_history.append(entry)

    if changed:
        collection.update_one(
            { "_id": product["_id"] },
            { "$set": { "price_history": new_history } }
        )
        fixed += 1

print(f"\nProduits vérifiés  : {checked}")
print(f"Produits corrigés  : {fixed}")
print("Fix terminé ✅")

client.close()
