"""
Script de diagnostic — inspecte les vraies valeurs en base
pour subcategory=None et les marques restantes
"""
import os
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://mariembouaziz:mariem1234@cluster0.dlbfsmd.mongodb.net/"
MONGO_DB  = "ecommerce_db"
MONGO_COL = "products"

client     = MongoClient(MONGO_URI)
collection = client[MONGO_DB][MONGO_COL]

print("=" * 60)
print("DIAGNOSTIC — types réels des valeurs en base")
print("=" * 60)

# ── 1. Inspecter les documents avec subcategory "None"-like
print("\n🔍 Échantillon subcategory problématiques (20 docs) :")
pipeline = [
    {"$match": {"subcategory": {"$in": [None, "None", "none", ""]}}},
    {"$project": {"subcategory": 1, "name": 1, "_id": 0}},
    {"$limit": 20}
]
for doc in collection.aggregate(pipeline):
    subcat = doc.get("subcategory")
    print(f"  type={type(subcat).__name__:<8}  repr={repr(subcat):<15}  name={doc.get('name','')[:40]}")

# ── 2. Compter chaque variante exacte
print("\n📊 Comptage exact des variantes subcategory vides/null :")
for val in [None, "None", "none", "", "null"]:
    count = collection.count_documents({"subcategory": val})
    print(f"  subcategory={repr(val):<10} → {count} documents")

count_missing = collection.count_documents({"subcategory": {"$exists": False}})
print(f"  subcategory absent (champ inexistant) → {count_missing} documents")

# ── 3. Vérifier s'il reste des marques non normalisées
print("\n📊 Marques suspectes restantes :")
suspects = ["Hp", "LENOVO", "ASUS", "DELL", "LOGITECH", "KARCHER",
            "REDRAGON", "Unknown", "unknown", "tunisianet", "False"]
for brand in suspects:
    count = collection.count_documents({"brand": brand})
    if count > 0:
        print(f"  brand={repr(brand):<20} → {count} documents")

# ── 4. Vérifier un doc None pour voir le type BSON réel
print("\n🔬 Type BSON réel d'un doc avec subcategory=None :")
doc = collection.find_one({"subcategory": "None"})
if doc:
    print(f"  Trouvé (string 'None') : name={doc.get('name','')[:50]}")
else:
    doc = collection.find_one({"subcategory": None})
    if doc:
        print(f"  Trouvé (null BSON)    : name={doc.get('name','')[:50]}")
    else:
        doc = collection.find_one({"subcategory": {"$exists": False}})
        if doc:
            print(f"  Trouvé (champ absent) : name={doc.get('name','')[:50]}")
        else:
            print("  Aucun document avec subcategory None/null/absent trouvé")

client.close()
print("\n✅ Diagnostic terminé")
