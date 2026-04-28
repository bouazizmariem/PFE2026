"""
normalize_mongodb.py  — v3
──────────────────────────
Corrections v3 :
  1. Brands  : scan total — corrige casse + valeurs parasites
  2. Subcats : fix du cas subcategory=null en base (filtre explicite $unset)

Usage :
    python normalize_mongodb.py

Variables d'environnement (optionnelles) :
    MONGO_URI  : URI de connexion
    MONGO_DB   : Nom de la base   (défaut: ecommerce_db)
    MONGO_COL  : Nom de la collection (défaut: products)
"""

import os
from pymongo import MongoClient, UpdateOne
from normalize_brand import normalize_brand
from normalize_subcategory import normalize_subcategory


# ── CONFIGURATION ─────────────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://mariembouaziz:mariem1234@cluster0.dlbfsmd.mongodb.net/")
MONGO_DB  = os.getenv("MONGO_DB",  "ecommerce_db")
MONGO_COL = os.getenv("MONGO_COL", "products")

BATCH_SIZE = 500


# ── HELPERS ───────────────────────────────────────────────────────────────────

def build_brand_update(doc: dict):
    """
    Construit un UpdateOne si la marque normalisée diffère de la valeur brute.
    Retourne None si aucun changement n'est requis.
    """
    raw_brand  = doc.get("brand") or ""
    name       = doc.get("name")  or ""
    normalized = normalize_brand(raw_brand, name)

    if normalized != raw_brand:
        return UpdateOne(
            {"_id": doc["_id"]},
            {"$set": {"brand": normalized}}
        )
    return None


def build_subcategory_update(doc: dict):
    """
    Construit un UpdateOne si la sous-catégorie normalisée diffère.
    Cas traités :
      - subcategory=None/null en base   → $unset
      - subcategory=valeur parasite     → $unset
      - subcategory=variante            → $set forme canonique
    Retourne None si aucun changement n'est requis.
    """
    raw_sub    = doc.get("subcategory")         # peut être None (null BSON)
    raw_str    = raw_sub if raw_sub else ""     # normalisation pour traitement
    normalized = normalize_subcategory(raw_str)

    # Cas 1 : subcategory déjà None en base ET normalize retourne None → rien à faire
    if raw_sub is None and normalized is None:
        return None

    # Cas 2 : valeur identique → rien à faire
    if normalized == raw_sub:
        return None

    # Cas 3 : normalize retourne None → supprimer le champ
    if normalized is None:
        return UpdateOne(
            {"_id": doc["_id"]},
            {"$unset": {"subcategory": ""}}
        )

    # Cas 4 : nouvelle valeur canonique → mettre à jour
    return UpdateOne(
        {"_id": doc["_id"]},
        {"$set": {"subcategory": normalized}}
    )


# ── TRAITEMENT PAR BATCH ──────────────────────────────────────────────────────

def flush_batch(collection, operations: list, label: str) -> int:
    if not operations:
        return 0
    result   = collection.bulk_write(operations, ordered=False)
    modified = result.modified_count
    print(f"  └─ batch envoyé : {len(operations):>4} ops → {modified:>4} modifiés ({label})")
    return modified


# ── NORMALISATION MARQUES ─────────────────────────────────────────────────────

def normalize_brands(collection) -> dict:
    """
    Parcourt TOUS les documents et normalise les marques.
    Corrige :
      - Valeurs parasites  : Unknown, tunisianet, False...
      - Variantes de casse : Hp→HP, LENOVO→Lenovo, ASUS→Asus...
    """
    print("\n📦 Normalisation des MARQUES")
    print("─" * 50)

    total = collection.count_documents({})
    print(f"  Documents à traiter : {total}")

    ops       = []
    processed = 0
    modified  = 0

    cursor = collection.find({}, {"_id": 1, "brand": 1, "name": 1})

    for doc in cursor:
        op = build_brand_update(doc)
        if op:
            ops.append(op)

        processed += 1

        if len(ops) >= BATCH_SIZE:
            modified += flush_batch(collection, ops, "brands")
            ops = []

        if processed % 5000 == 0:
            print(f"  ... {processed}/{total} traités")

    modified += flush_batch(collection, ops, "brands")

    print(f"\n  ✅ Marques normalisées : {modified} / {total}")
    return {"total": total, "modified": modified}


# ── NORMALISATION SOUS-CATÉGORIES ─────────────────────────────────────────────

def normalize_subcategories(collection) -> dict:
    """
    Parcourt tous les documents et normalise les sous-catégories.
    Traite aussi les subcategory=null stockés en base (448 documents).
    """
    print("\n📦 Normalisation des SOUS-CATÉGORIES")
    print("─" * 50)

    # Étape 1 : supprimer les champs subcategory=null explicitement en base
    # (cas non attrapé en v2 car $unset sur null n'est pas comptabilisé)
    null_result = collection.update_many(
        {"subcategory": None},
        {"$unset": {"subcategory": ""}}
    )
    if null_result.modified_count:
        print(f"  🧹 Champs subcategory=null supprimés : {null_result.modified_count}")

    total = collection.count_documents({})
    print(f"  Documents à traiter : {total}")

    ops       = []
    processed = 0
    modified  = 0

    cursor = collection.find({}, {"_id": 1, "subcategory": 1})

    for doc in cursor:
        op = build_subcategory_update(doc)
        if op:
            ops.append(op)

        processed += 1

        if len(ops) >= BATCH_SIZE:
            modified += flush_batch(collection, ops, "subcategories")
            ops = []

        if processed % 5000 == 0:
            print(f"  ... {processed}/{total} traités")

    modified += flush_batch(collection, ops, "subcategories")

    total_fixed = null_result.modified_count + modified
    print(f"\n  ✅ Sous-catégories normalisées : {total_fixed} (dont {null_result.modified_count} null supprimés + {modified} variantes corrigées)")
    return {"total": total, "modified": total_fixed}


# ── RAPPORTS ──────────────────────────────────────────────────────────────────

def print_brand_distribution(collection, label: str, limit: int = 20):
    print(f"\n📊 Distribution marques ({label}) — top {limit} :")
    pipeline = [
        {"$group": {"_id": "$brand", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    for doc in collection.aggregate(pipeline):
        print(f"  {str(doc['_id']):<35} : {doc['count']}")


def print_subcategory_distribution(collection, label: str, limit: int = 20):
    print(f"\n📊 Distribution sous-catégories ({label}) — top {limit} :")
    pipeline = [
        {"$group": {"_id": "$subcategory", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    for doc in collection.aggregate(pipeline):
        print(f"  {str(doc['_id']):<50} : {doc['count']}")


def print_null_subcategory_count(collection, label: str):
    """Compte les documents sans champ subcategory ou avec null."""
    count = collection.count_documents(
        {"$or": [{"subcategory": {"$exists": False}}, {"subcategory": None}]}
    )
    print(f"\n  🔍 Documents sans subcategory ({label}) : {count}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  NORMALISATION MONGODB v3 — brands & subcategories")
    print("=" * 60)
    print(f"  URI        : {MONGO_URI}")
    print(f"  Base       : {MONGO_DB}")
    print(f"  Collection : {MONGO_COL}")
    print(f"  Batch size : {BATCH_SIZE}")

    client     = MongoClient(MONGO_URI)
    db         = client[MONGO_DB]
    collection = db[MONGO_COL]

    total_docs = collection.count_documents({})
    print(f"\n  Total documents : {total_docs}")

    # Rapports AVANT
    print_brand_distribution(collection, "AVANT")
    print_subcategory_distribution(collection, "AVANT")
    print_null_subcategory_count(collection, "AVANT")

    # Normalisation
    brand_stats  = normalize_brands(collection)
    subcat_stats = normalize_subcategories(collection)

    # Rapports APRÈS
    print_brand_distribution(collection, "APRÈS")
    print_subcategory_distribution(collection, "APRÈS")
    print_null_subcategory_count(collection, "APRÈS")

    # Résumé
    print("\n" + "=" * 60)
    print("  RÉSUMÉ")
    print("=" * 60)
    print(f"  Documents total           : {total_docs}")
    print(f"  Marques corrigées         : {brand_stats['modified']} / {brand_stats['total']}")
    print(f"  Sous-catégories corrigées : {subcat_stats['modified']} / {subcat_stats['total']}")
    print("=" * 60)
    print("  ✅ Normalisation v3 terminée")

    client.close()


if __name__ == "__main__":
    main()