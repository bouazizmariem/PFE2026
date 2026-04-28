# ── NORMALIZE_BRAND.PY ────────────────────────────────────────────────────────
# Normalisation des marques : casse, tirets, espaces, valeurs parasites
# + extraction de marque depuis le nom du produit si brand = Unknown

import re


# ── VALEURS À TRAITER COMME INCONNUES ────────────────────────────────────────
UNKNOWN_BRANDS = {
    "", "sans marque", "sans-marque", "sans fabricant", "sans-fabricant",
    "noname", "no name", "unknown", "false", "none", "null",
    "tunisianet", "spacenet", "mytek",
    "compatible apple", "compatible hp",
    "compatible asus", "compatible dell",
    "compatible lenovo", "compatible msi",
    "compatible acer",
}


# ── MAPPING CANONIQUE ─────────────────────────────────────────────────────────
BRAND_MAPPING = {

    # ── INFORMATIQUE ──────────────────────────────────────────────────────────
    "Hp": "HP", "hp": "HP", "HP": "HP", "HPE": "HPE",
    "Lenovo": "Lenovo", "LENOVO": "Lenovo",
    "Asus": "Asus", "ASUS": "Asus", "Republic Of Gamer": "Asus",
    "Dell": "Dell", "DELL": "Dell",
    "Acer": "Acer", "ACER": "Acer",
    "Msi": "MSI", "msi": "MSI", "MSI": "MSI",
    "Powered By MSI": "MSI", "POWERED-BY-MSI-ADVANCED": "MSI",
    "POWERED-BY-MSI-ESSENTIAL": "MSI", "POWERED-BY-MSI-ULTIMATE": "MSI",
    "Apple": "Apple", "APPLE": "Apple",
    "Microsoft": "Microsoft", "MICROSOFT": "Microsoft",
    "Intel": "Intel", "INTEL": "Intel",
    "Amd": "AMD", "amd": "AMD", "AMD": "AMD", "AMD RYZEN": "AMD",
    "Gigabyte": "Gigabyte", "GIGABYTE": "Gigabyte",
    "Asrock": "ASRock", "ASROCK": "ASRock", "ASRock": "ASRock",
    "Zotac": "Zotac", "ZOTAC": "Zotac",

    # ── PÉRIPHÉRIQUES / GAMING ────────────────────────────────────────────────
    "Logitech": "Logitech", "LOGITECH": "Logitech",
    "Redragon": "Redragon", "REDRAGON": "Redragon",
    "Razer": "Razer", "RAZER": "Razer",
    "Hyperx": "HyperX", "HYPERX": "HyperX", "HyperX": "HyperX",
    "Spirit of Gamer": "Spirit of Gamer", "SPIRIT OF GAMER": "Spirit of Gamer",
    "SPIRIT-OF-GAMER": "Spirit of Gamer", "Spirit Of Gamer": "Spirit of Gamer",
    "White Shark": "White Shark", "WHITE SHARK": "White Shark",
    "WHITE-SHARK": "White Shark",
    "Cooler Master": "Cooler Master", "COOLER MASTER": "Cooler Master",
    "COOLER-MASTER": "Cooler Master",
    "Deepcool": "DeepCool", "DEEPCOOL": "DeepCool", "DeepCool": "DeepCool",
    "Havit": "Havit", "HAVIT": "Havit",
    "Rivacase": "Rivacase", "RIVACASE": "Rivacase",

    # ── STOCKAGE ──────────────────────────────────────────────────────────────
    "Sandisk": "SanDisk", "SANDISK": "SanDisk", "SanDisk": "SanDisk",
    "Seagate": "Seagate", "SEAGATE": "Seagate",
    "Western Digital": "Western Digital", "WESTERN DIGITAL": "Western Digital",
    "WESTERN-DIGITAL": "Western Digital",
    "Kingston": "Kingston", "KINGSTON": "Kingston",
    "Adata": "ADATA", "ADATA": "ADATA",
    "Silicon Power": "Silicon Power", "SILICON POWER": "Silicon Power",
    "SILICON-POWER": "Silicon Power",
    "Hiksemi": "Hiksemi", "HIKSEMI": "Hiksemi",
    "Twinmos": "TwinMos", "TWINMOS": "TwinMos", "TwinMos": "TwinMos",
    "Pny": "PNY", "pny": "PNY", "PNY": "PNY",

    # ── TÉLÉVISEURS / AUDIOVISUEL ─────────────────────────────────────────────
    "Samsung": "Samsung", "SAMSUNG": "Samsung",
    "Lg": "LG", "lg": "LG", "LG": "LG",
    "Hisense": "Hisense", "HiSense": "Hisense", "HISENSE": "Hisense",
    "hisense": "Hisense",
    "Tcl": "TCL", "tcl": "TCL", "TCL": "TCL",
    "Telefunken": "Telefunken", "TELEFUNKEN": "Telefunken",
    "Sony": "Sony", "SONY": "Sony",
    "Philips": "Philips", "PHILIPS": "Philips",
    "Sharp": "Sharp", "SHARP": "Sharp",
    "Toshiba": "Toshiba", "TOSHIBA": "Toshiba",
    "Jbl": "JBL", "JBL": "JBL",
    "Jabra": "Jabra", "JABRA": "Jabra",

    # ── ÉLECTROMÉNAGER ────────────────────────────────────────────────────────
    "Bosch": "Bosch", "BOSCH": "Bosch",
    "Whirlpool": "Whirlpool", "WHIRLPOOL": "Whirlpool",
    "Beko": "Beko", "BEKO": "Beko",
    "Brandt": "Brandt", "BRANDT": "Brandt",
    "Ariston": "Ariston", "ARISTON": "Ariston",
    "Candy": "Candy", "CANDY": "Candy",
    "Hoover": "Hoover", "HOOVER": "Hoover",
    "Moulinex": "Moulinex", "MOULINEX": "Moulinex",
    "Tefal": "Tefal", "TEFAL": "Tefal",
    "Kenwood": "Kenwood", "KENWOOD": "Kenwood",
    "Rowenta": "Rowenta", "ROWENTA": "Rowenta",
    "Braun": "Braun", "BRAUN": "Braun",
    "Karcher": "Kärcher", "KARCHER": "Kärcher",
    "Russell hobbs": "Russell Hobbs", "Russell Hobbs": "Russell Hobbs",
    "RUSSELL HOBBS": "Russell Hobbs", "RUSSELL-HOBBS": "Russell Hobbs",
    "Russel Hobbs": "Russell Hobbs",
    "Delonghi": "De'Longhi", "DeLonghi": "De'Longhi",
    "DELONGHI": "De'Longhi", "De'Longhi": "De'Longhi",
    "Nespresso": "Nespresso",
    "Midea": "Midea", "MIDEA": "Midea",
    "Condor": "Condor", "CONDOR": "Condor",

    # ── MARQUES LOCALES / TUNISIENNES ─────────────────────────────────────────
    "Biolux": "Biolux", "BIOLUX": "Biolux", "BioLux": "Biolux",
    "Florence": "Florence", "FLORENCE": "Florence",
    "Focus": "Focus", "FOCUS": "Focus",
    "Raf": "RAF", "RAF": "RAF",
    "Lexical": "Lexical", "LEXICAL": "Lexical",
    "Techwood": "Techwood", "TECHWOOD": "Techwood",
    "Mont Blanc": "Mont Blanc", "MontBlanc": "Mont Blanc",
    "MONTBLANC": "Mont Blanc", "Montblanc": "Mont Blanc",
    "Orient": "Orient", "ORIENT": "Orient",

    # ── DIVERS ────────────────────────────────────────────────────────────────
    "Xiaomi": "Xiaomi", "XIAOMI": "Xiaomi",
    "Advance": "Advance", "ADVANCE": "Advance",
    "Trust": "Trust", "TRUST": "Trust",
    "Aoc": "AOC", "AOC": "AOC",
    "Aqirys": "Aqirys", "AQIRYS": "Aqirys", "aqirys": "Aqirys",
    "Synology": "Synology",
    "Qnap": "QNAP", "QNAP": "QNAP",
    "Hikvision": "Hikvision", "HikVision": "Hikvision", "HIKVISION": "Hikvision",
    "D-Link": "D-Link", "DLINK": "D-Link",
    "Tp-Link": "TP-Link", "TP-LINK": "TP-Link", "TP-Link": "TP-Link",
    "Kaspersky": "Kaspersky", "KASPERSKY": "Kaspersky",
    "Floria": "Floria", "FLORIA": "Floria",
    "Coala": "Coala", "COALA": "Coala",
    "Livoo": "Livoo", "LIVOO": "Livoo",
    "Hama": "Hama", "HAMA": "Hama", "hama": "Hama",
    "Wacom": "Wacom", "WACOM": "Wacom",
    "Gembird": "Gembird", "GEMBIRD": "Gembird", "gembird": "Gembird",
    "Sandberg": "Sandberg", "SANDBERG": "Sandberg", "sandberg": "Sandberg",
    "Meetion": "Meetion", "MEETION": "Meetion",
    "Marvo": "Marvo",
    "Jedel": "Jedel", "JEDEL": "Jedel",
    "Baracuda": "Baracuda", "BARACUDA": "Baracuda",
    "Decakila": "Decakila", "DECAKILA": "Decakila",
    "Joker": "Joker", "JOKER": "Joker",
    "Platinet": "Platinet", "PLATINET": "Platinet",
    "Sbox": "SBOX", "SBOX": "SBOX",
    "Kiwi": "Kiwi", "KIWI": "Kiwi",
    "Bange": "Bange", "BANGE": "Bange",
    "Princess": "Princess", "PRINCESS": "Princess",
    "Fresh": "Fresh", "FRESH": "Fresh",
    "Sonifer": "Sonifer", "SONIFER": "Sonifer",
    "Inca": "INCA", "INCA": "INCA",
    "Newstar": "Newstar", "NEWSTAR": "Newstar", "New Star": "Newstar",
    "Arctic Hunter": "Arctic Hunter", "ARCTIC-HUNTER": "Arctic Hunter",
}


# ── INDEX INSENSIBLE À LA CASSE ───────────────────────────────────────────────
_BRAND_MAPPING_LOWER = {k.lower(): v for k, v in BRAND_MAPPING.items()}


# ── LISTE DES MARQUES CANONIQUES POUR EXTRACTION DEPUIS LE NOM ───────────────
# Triées par longueur décroissante : matcher "Spirit of Gamer" avant "Spirit",
# "Western Digital" avant "Western", "Cooler Master" avant "Cooler"

KNOWN_BRANDS_CANONICAL = sorted(
    set(BRAND_MAPPING.values()),
    key=lambda x: len(x),
    reverse=True
)

# Patterns pré-compilés pour performance (un par marque canonique)
_BRAND_PATTERNS = [
    (canonical, re.compile(
        r"(?<![a-zA-Z0-9])" + re.escape(canonical.lower()) + r"(?![a-zA-Z0-9])"
    ))
    for canonical in KNOWN_BRANDS_CANONICAL
]


def _extract_brand_from_name(name: str) -> str | None:
    """
    Cherche une marque connue dans le nom du produit.
    Retourne la forme canonique si trouvée, None sinon.

    Exemples :
        "PC Portable HP 15s-fq5000nk"     → "HP"
        "Réfrigérateur Samsung RT38K5400" → "Samsung"
        "Clavier Mécanique MSI Vigor GK50"→ "MSI"
        "Aspirateur 2200W turbo brosse"   → None
    """
    if not name:
        return None

    name_lower = name.lower()

    for canonical, pattern in _BRAND_PATTERNS:
        if pattern.search(name_lower):
            return canonical

    return None


# ── FONCTION PRINCIPALE ───────────────────────────────────────────────────────

def normalize_brand(brand: str, name: str = "") -> str:
    """
    Normalise une marque brute vers sa forme canonique.

    Priorité :
      1. Brand nulle / vide / parasite
            → cherche dans name via _extract_brand_from_name()
            → trouvée  : retourne la marque extraite
            → non trouvée : retourne "Sans Marque"
      2. Correspondance exacte dans BRAND_MAPPING
      3. Correspondance insensible à la casse dans BRAND_MAPPING
      4. Fallback : valeur strip()ée telle quelle
    """
    if not brand:
        extracted = _extract_brand_from_name(name)
        return extracted if extracted else "Sans Marque"

    brand = brand.strip()

    # 1. Valeurs parasites → tenter extraction depuis le nom
    if brand.lower() in UNKNOWN_BRANDS:
        extracted = _extract_brand_from_name(name)
        return extracted if extracted else "Sans Marque"

    # 2. Correspondance exacte
    if brand in BRAND_MAPPING:
        return BRAND_MAPPING[brand]

    # 3. Correspondance insensible à la casse
    if brand.lower() in _BRAND_MAPPING_LOWER:
        return _BRAND_MAPPING_LOWER[brand.lower()]

    # 4. Fallback
    return brand