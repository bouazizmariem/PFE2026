import re
import unicodedata


# ── MAPPING CLÉ BRUTE → CLÉ CANONIQUE ────────────────────────────────────────
# Les clés ici sont les formes BRUTES (avant slugify) venant des scrapers.
# Les clés déjà slugifiées (venant des fichiers déjà nettoyés) sont dans
# SLUGIFIED_KEY_MAPPING plus bas.

KEY_MAPPING = {

    # ── CAPACITÉ / VOLUME ─────────────────────────────────────────────
    "Capacité":                                 "capacite",
    "Capacite":                                 "capacite",
    "Capacité D'eau":                           "capacite",
    "Capacité du réservoir":                    "capacite",
    "Volume brut":                              "capacite",
    "Volume":                                   "capacite",
    "Capacité / Taille":                        "capacite",

    # ── CLASSE ÉNERGÉTIQUE ────────────────────────────────────────────
    "Classe Energétique":                       "classe_energetique",
    "Classe Énergétique":                       "classe_energetique",
    "Classe énergétique":                       "classe_energetique",
    "Classe Energitique":                       "classe_energetique",
    "Classe de Températures":                   "classe_temperatures",

    # ── PUISSANCE ─────────────────────────────────────────────────────
    "Puissance":                                "puissance",
    "Puissance Nominale":                       "puissance",
    "Puissance alimentation":                   "puissance",

    # ── TYPE (générique) ──────────────────────────────────────────────
    "Type":                                     "type",
    "Type de Réfrigérateur":                    "type",
    "Type de climatiseur":                      "type",
    "Type de machine":                          "type",
    "Type machine":                             "type",
    "Type du café":                             "type",
    "Type de Machine à Café":                   "type",
    "Type de Plaque":                           "type",
    "Type de Hachoir":                          "type",
    "Type d'aspirateur":                        "type",
    "Type de Bac à Poussière":                  "type",
    "Type de Chauffage":                        "type",
    "Type de Casque":                           "type",

    # ── TYPE ÉCRAN ────────────────────────────────────────────────────
    "Type Ecran":                               "type_ecran",
    "Type D'Écran":                             "type_ecran",
    "Type de technologie de l'écran":           "type_ecran",

    # ── TYPE DISQUE / STOCKAGE ────────────────────────────────────────
    "Type Disque Dur":                          "type_disque",
    "Type de disque SSD":                       "type_disque",
    "Type de disque":                           "type_disque",
    "Format de Disque":                         "type_disque",
    "Format de disque":                         "type_disque",
    "Disque Dur":                               "disque_dur",
    "Stockage":                                 "stockage",
    "Capacité de stockage":                     "stockage",

    # ── TYPE PROCESSEUR ───────────────────────────────────────────────
    "Type de Processeur":                       "type_processeur",
    "Type processeur":                          "type_processeur",
    "Processeur":                               "processeur",
    "processeur":                               "processeur",
    "Réf processeur":                           "ref_processeur",
    "Génération de processeur INTEL":           "generation_processeur",
    "Fréquence Processeur":                     "frequence_processeur",

    # ── REFROIDISSEMENT ───────────────────────────────────────────────
    "Système de refroidissement":               "systeme_refroidissement",
    "Système de Refroidissement":               "systeme_refroidissement",
    "Système de dégivrage":                     "systeme_refroidissement",

    # ── COULEUR ───────────────────────────────────────────────────────
    "Couleur":                                  "couleur",

    # ── GARANTIE ──────────────────────────────────────────────────────
    "Garantie":                                 "garantie",

    # ── INVERTER / SMART ──────────────────────────────────────────────
    "Inverter":                                 "inverter",
    "Smart":                                    "smart",
    "Smart TV":                                 "smart",

    # ── DISTRIBUTEUR ──────────────────────────────────────────────────
    "Distributeur":                             "distributeur",
    "Avec Distributeur":                        "distributeur",

    # ── CLIMATISATION ─────────────────────────────────────────────────
    "Tropicalisé":                              "tropicalise",
    "Surface couverte clim":                    "surface_couverte",
    "Option(s) Climatiseur":                    "options",
    "Mode":                                     "mode",
    "Nombre de vitesses":                       "nombre_vitesses",
    "Accessoires Climatisation":                "accessoires",

    # ── ÉLECTROMÉNAGER ────────────────────────────────────────────────
    "Nombre de Couverts":                       "nombre_couverts",
    "Nombre de Feux":                           "nombre_feux",
    "Nombre de Programmes":                     "nombre_programmes",
    "Nombre De Tasses":                         "nombre_tasses",
    "Commande":                                 "commande",
    "Alimentation":                             "alimentation",
    "Vapeur":                                   "vapeur",
    "Thermocouple":                             "thermocouple",
    "Encastrable":                              "encastrable",
    "Niveau de Chaleur":                        "niveau_chaleur",
    "Longueur du câble":                        "longueur_cable",
    "Largeur":                                  "largeur",
    "Afficheur":                                "afficheur",

    # ── MÉMOIRE ───────────────────────────────────────────────────────
    "Mémoire Ram":                              "memoire_ram",
    "RAM":                                      "memoire_ram",
    "Mémoire":                                  "memoire_ram",
    "Capacité de la mémoire":                   "memoire_ram",
    "Mémoire Vive de la Carte Graphique":       "memoire_gpu",
    "mémoire graphique":                        "memoire_gpu",
    "Fréquence mémoire max":                    "frequence_memoire",
    "Vitesse Mémoire":                          "frequence_memoire",
    "Fréquence mémoire":                        "frequence_memoire",

    # ── CARTE GRAPHIQUE ───────────────────────────────────────────────
    "Carte Graphique":                          "carte_graphique",
    "Chipset graphique":                        "carte_graphique",
    "Réf Carte Graphique":                      "ref_carte_graphique",
    "Réf Carte graphique":                      "ref_carte_graphique",

    # ── ÉCRAN ─────────────────────────────────────────────────────────
    "Ecran":                                    "ecran",
    "Ecran intégré":                            "ecran",
    "Taille de l'écran":                        "taille_ecran",
    "Taille Ecran":                             "taille_ecran",
    "Résolution":                               "resolution",
    "Taux de Rafraîchissement":                 "taux_rafraichissement",
    "Luminosité":                               "luminosite",
    "Temps de réponse":                         "temps_reponse",
    "Rapport de contraste":                     "rapport_contraste",

    # ── CONNECTIVITÉ ──────────────────────────────────────────────────
    "Connectivité":                             "connectivite",
    "Connectivités":                            "connectivite",
    "Wifi":                                     "wifi",
    "Bluetooth":                                "bluetooth",
    "Ports":                                    "ports",
    "Nombre de ports":                          "nombre_ports",

    # ── SYSTÈME D'EXPLOITATION ────────────────────────────────────────
    "Système d'exploitation":                   "systeme_exploitation",
    "Système":                                  "systeme_exploitation",

    # ── PHYSIQUE ──────────────────────────────────────────────────────
    "Poids":                                    "poids",
    "Poids des produits":                       "poids",
    "Dimensions":                               "dimensions",
    "Dimension":                                "dimensions",

    # ── BATTERIE / AUTONOMIE ──────────────────────────────────────────
    "Autonomie":                                "autonomie",
    "Durée de vie maximale de la batterie":     "autonomie",
    "Capacité de batterie":                     "batterie",

    # ── DIVERS INFORMATIQUE ───────────────────────────────────────────
    "Gamer":                                    "gamer",
    "RGB":                                      "rgb",
    "Webcam":                                   "webcam",
    "Microphone":                               "microphone",
    "Haut-parleur":                             "haut_parleur",
    "Norme Clavier":                            "norme_clavier",
    "Format de carte mère":                     "format_carte_mere",
    "Format Du Boitier":                        "format_boitier",
    "Interface":                                "interface",
    "Fréquence":                                "frequence",
}


# ── MAPPING DES CLÉS DÉJÀ SLUGIFIÉES (issues des fichiers nettoyés) ───────────
# Ces clés arrivent déjà en snake_case depuis les scrapers Spacenet/Tunisianet
# ou après un premier passage de normalize_specs. On les harmonise ici.

SLUGIFIED_KEY_MAPPING = {

    # ── COULEUR ───────────────────────────────────────────────────────
    "color":                                    "couleur",

    # ── GARANTIE variantes ────────────────────────────────────────────
    "garante":                                  "garantie",
    "granatie":                                 "garantie",
    "grantie":                                  "garantie",
    "garantie_3_ans_garantie_compresseur":      "garantie",

    # ── CLASSE ÉNERGÉTIQUE variantes ──────────────────────────────────
    "class_energetique":                        "classe_energetique",
    "classe_energetique_en_froid":              "classe_energetique",
    "classe_energetique_froid":                 "classe_energetique",
    "classe_enerqetique":                       "classe_energetique",
    "classe_d_efficacite_energetique":          "classe_energetique",

    # ── PUISSANCE variantes ───────────────────────────────────────────
    "puisaance":                                "puissance",
    "puissance_moteur":                         "puissance",
    "puissance_absorbee":                       "puissance",
    "puissance_totale":                         "puissance",

    # ── CAPACITÉ variantes ────────────────────────────────────────────
    "capacite_nette_en_litres":                 "capacite",
    "capacite_totale":                          "capacite",
    "capacite_net":                             "capacite",
    "capacite_utile":                           "capacite",
    "capacite_de_lavage_kg":                    "capacite_de_lavage",

    # ── MÉMOIRE RAM variantes ─────────────────────────────────────────
    "capacite_ram":                             "memoire_ram",
    "capacite_memoire":                         "memoire_ram",
    "capacite_maximale_de_ram":                 "memoire_ram",
    "capacite_de_memoire":                      "memoire_ram",
    "memoire_flash":                            "memoire_ram",

    # ── STOCKAGE variantes ────────────────────────────────────────────
    "memoire_de_stockage":                      "stockage",

    # ── SYSTÈME D'EXPLOITATION variantes ──────────────────────────────
    "systeme_d_exploitation":                   "systeme_exploitation",
    "systeme_d_exploitation_compatible":        "systeme_exploitation",
    "systeme_d_exploitation_pris_en_charge":    "systeme_exploitation",
    "systeme_d_exploitation_requis":            "systeme_exploitation",
    "systeme_d_exploitation_requise":           "systeme_exploitation",
    "systeme_d_exploitation_supportes":         "systeme_exploitation",
    "systemes_d_exploitation":                  "systeme_exploitation",
    "systemes_d_exploitation_compatible":       "systeme_exploitation",
    "systemes_d_exploitation_compatibles":      "systeme_exploitation",
    "systemes_d_exploitation_pris_en_charge":   "systeme_exploitation",
    "systemes_d_exploitation_supportes":        "systeme_exploitation",
    "systeme_operateur":                        "systeme_exploitation",
    "version_systeme":                          "systeme_exploitation",

    # ── PROCESSEUR variantes ──────────────────────────────────────────
    "microprocesseur":                          "processeur",
    "processeur_graphique":                     "carte_graphique",
    "graphiques":                               "carte_graphique",

    # ── TAILLE ÉCRAN variantes ────────────────────────────────────────
    "taille_de_l_ecran":                        "taille_ecran",
    "taille_de_notebook":                       "taille_ecran",
    "taille_de_pc_portable":                    "taille_ecran",
    "taille_pc_portable":                       "taille_ecran",
    "taille_pc":                                "taille_ecran",

    # ── RÉSOLUTION variantes ──────────────────────────────────────────
    "resolution_d_ecran":                       "resolution",
    "resolution_maximale":                      "resolution",
    "resolution_video":                         "resolution",
    "resolution_video_max":                     "resolution",

    # ── TAUX DE RAFRAÎCHISSEMENT variantes ────────────────────────────
    "frequence_de_rafraichissement":            "taux_rafraichissement",
    "taux_de_rafraichissement":                 "taux_rafraichissement",

    # ── CONNECTIVITÉ variantes ────────────────────────────────────────
    "connectivite_sans_fil":                    "connectivite",
    "connectivite_double":                      "connectivite",
    "connexion":                                "connectivite",
    "connexion_principale":                     "connectivite",
    "communication_sans_fil":                   "wifi",

    # ── POIDS variantes ───────────────────────────────────────────────
    "poid":                                     "poids",
    "poids_net":                                "poids",

    # ── DIMENSIONS variantes ──────────────────────────────────────────
    "dimesions":                                "dimensions",
    "dimension":                                "dimensions",

    # ── BATTERIE variantes ────────────────────────────────────────────
    "capacite_batterie":                        "batterie",
    "capacite_de_la_batterie":                  "batterie",
    "capacite_mah":                             "batterie",

    # ── AUTONOMIE variantes ───────────────────────────────────────────
    "autonomie_batterie":                       "autonomie",
    "autonomie_de_la_batterie":                 "autonomie",
    "autonomie_baterie":                        "autonomie",
    "duree_de_vie_de_la_batterie":              "autonomie",

    # ── NOMBRE DE FEUX (tunisianet) ───────────────────────────────────
    "feux":                                     "nombre_feux",

    # ── NOMBRE DE PORTS variantes ─────────────────────────────────────
    "nombre_de_port":                           "nombre_ports",
    "nombres_de_ports":                         "nombre_ports",

    # ── CLÉS PARASITES À SUPPRIMER ────────────────────────────────────
    "promo":                                    None,   # donnée commerciale
}


# ── NORMALISATION DES VALEURS ─────────────────────────────────────────────────

def _normalize_storage(value):
    """8Go, 8 Go, 8GB, 512go, 1To → '8 Go', '512 Go', '1 To'"""
    match = re.search(r"(\d+)\s*(go|gb|mo|mb|to|tb)", value.lower())
    if match:
        num, unit = match.groups()
        unit_map = {
            "go": "Go", "gb": "Go",
            "mo": "Mo", "mb": "Mo",
            "to": "To", "tb": "To",
        }
        return f"{num} {unit_map[unit]}"
    return value


def _normalize_screen_size(value):
    """'15.6 pouces', '15,6"', '27 pouces' → '15.6"', '27"'"""
    match = re.search(r"(\d+[.,]\d+|\d+)", value)
    if match:
        return f"{match.group(1).replace(',', '.')}\"" 
    return value


def _normalize_bool(value):
    """Oui/Yes/True/1 → 'Oui' | Non/No/False/0 → 'Non'"""
    if str(value).lower() in ("oui", "yes", "true", "1"):
        return "Oui"
    if str(value).lower() in ("non", "no", "false", "0"):
        return "Non"
    return value


def _normalize_garantie(value):
    """'2 ans constructeur', '12 mois' → '2 ans', '12 mois'"""
    match = re.search(r"\d+\s*(ans|an|mois)", value.lower())
    if match:
        return match.group(0)
    return value


def _normalize_frequence(value):
    """'2400mhz', '2400 MHz', '3.5ghz' → '2400 MHz', '3.5 GHz'"""
    match = re.search(r"(\d+[.,]?\d*)\s*(mhz|ghz)", value.lower())
    if match:
        num, unit = match.groups()
        unit_map = {"mhz": "MHz", "ghz": "GHz"}
        return f"{num.replace(',', '.')} {unit_map[unit]}"
    return value


# Associe chaque clé canonique à sa fonction de normalisation
VALUE_NORMALIZERS = {
    "memoire_ram":          _normalize_storage,
    "memoire_gpu":          _normalize_storage,
    "stockage":             _normalize_storage,
    "disque_dur":           _normalize_storage,
    "batterie":             _normalize_storage,
    "taille_ecran":         _normalize_screen_size,
    "wifi":                 _normalize_bool,
    "bluetooth":            _normalize_bool,
    "inverter":             _normalize_bool,
    "smart":                _normalize_bool,
    "webcam":               _normalize_bool,
    "microphone":           _normalize_bool,
    "vapeur":               _normalize_bool,
    "encastrable":          _normalize_bool,
    "garantie":             _normalize_garantie,
    "frequence_processeur": _normalize_frequence,
    "frequence_memoire":    _normalize_frequence,
}


# ── UTILITAIRES ───────────────────────────────────────────────────────────────

def _slugify(key: str) -> str:
    """Transforme une clé quelconque en snake_case ASCII."""
    key = unicodedata.normalize("NFD", key)
    key = "".join(c for c in key if unicodedata.category(c) != "Mn")
    key = key.lower()
    key = re.sub(r"[^a-z0-9]+", "_", key)
    key = key.strip("_")
    return key


# Index insensible à la casse construits une seule fois
_KEY_MAPPING_LOWER          = {k.lower(): v for k, v in KEY_MAPPING.items()}
_SLUGIFIED_KEY_MAPPING_LOWER = {k.lower(): v for k, v in SLUGIFIED_KEY_MAPPING.items()}


# ── FONCTION PRINCIPALE ───────────────────────────────────────────────────────

def normalize_specs(specs: dict) -> dict:
    """
    Normalise les clés ET les valeurs d'un dict de spécifications.

    Priorité de résolution pour chaque clé :
      1. Correspondance exacte dans KEY_MAPPING          (clés brutes scrapers)
      2. Correspondance insensible à la casse KEY_MAPPING
      3. Correspondance exacte dans SLUGIFIED_KEY_MAPPING (clés déjà slugifiées)
      4. Correspondance insensible à la casse SLUGIFIED_KEY_MAPPING
      5. Fallback : slugify générique

    Si la clé canonique est None → la spec est supprimée (clé parasite).
    """
    if not specs:
        return {}

    result = {}

    for raw_key, value in specs.items():
        if not raw_key or not value:
            continue

        key = raw_key.strip()

        _SENTINEL = object()  # valeur impossible pour distinguer "absent" de None

        # 1. Correspondance exacte KEY_MAPPING (formes brutes)
        canonical = KEY_MAPPING.get(key, _SENTINEL)

        # 2. Insensible à la casse KEY_MAPPING
        if canonical is _SENTINEL:
            canonical = _KEY_MAPPING_LOWER.get(key.lower(), _SENTINEL)

        # 3. Correspondance exacte SLUGIFIED_KEY_MAPPING (formes déjà slugifiées)
        if canonical is _SENTINEL:
            canonical = SLUGIFIED_KEY_MAPPING.get(key, _SENTINEL)

        # 4. Insensible à la casse SLUGIFIED_KEY_MAPPING
        if canonical is _SENTINEL:
            canonical = _SLUGIFIED_KEY_MAPPING_LOWER.get(key.lower(), _SENTINEL)

        # Clé parasite (None explicite dans un des mappings) → on ignore
        if canonical is None:
            continue

        # 5. Fallback slugify générique (clé inconnue)
        if canonical is _SENTINEL:
            canonical = _slugify(key)

        # Normaliser la valeur si un normalizer existe
        normalizer = VALUE_NORMALIZERS.get(canonical)
        if normalizer:
            try:
                value = normalizer(str(value))
            except Exception:
                pass  # conserver la valeur brute si le normalizer échoue

        result[canonical] = value

    return result