import re
import unicodedata


# Mapping clé brute → clé canonique normalisée
KEY_MAPPING = {

    # ── CAPACITÉ / VOLUME ──────────────────────────────────────────────
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

    # ── PUISSANCE ────────────────────────────────────────────────────
    "Puissance":                                "puissance",
    "Puissance Nominale":                       "puissance",
    "Puissance alimentation":                   "puissance",

    # ── TYPE (générique) ─────────────────────────────────────────────
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

    # ── TYPE ÉCRAN ───────────────────────────────────────────────────
    "Type Ecran":                               "type_ecran",
    "Type D'Écran":                             "type_ecran",
    "Type de technologie de l'écran":           "type_ecran",

    # ── TYPE DISQUE / STOCKAGE ───────────────────────────────────────
    "Type Disque Dur":                          "type_disque",
    "Type de disque SSD":                       "type_disque",
    "Type de disque":                           "type_disque",
    "Format de Disque":                         "type_disque",
    "Format de disque":                         "type_disque",
    "Disque Dur":                               "disque_dur",
    "Stockage":                                 "stockage",
    "Capacité de stockage":                     "stockage",

    # ── TYPE PROCESSEUR ──────────────────────────────────────────────
    "Type de Processeur":                       "type_processeur",
    "Type processeur":                          "type_processeur",
    "Processeur":                               "processeur",
    "processeur":                               "processeur",
    "Réf processeur":                           "ref_processeur",
    "Génération de processeur INTEL":           "generation_processeur",
    "Fréquence Processeur":                     "frequence_processeur",

    # ── REFROIDISSEMENT ──────────────────────────────────────────────
    "Système de refroidissement":               "systeme_refroidissement",
    "Système de Refroidissement":               "systeme_refroidissement",
    "Système de dégivrage":                     "systeme_refroidissement",

    # ── COULEUR ──────────────────────────────────────────────────────
    "Couleur":                                  "couleur",

    # ── GARANTIE ────────────────────────────────────────────────────
    "Garantie":                                 "garantie",

    # ── INVERTER / SMART ─────────────────────────────────────────────
    "Inverter":                                 "inverter",
    "Smart":                                    "smart",
    "Smart TV":                                 "smart",

    # ── DISTRIBUTEUR ────────────────────────────────────────────────
    "Distributeur":                             "distributeur",
    "Avec Distributeur":                        "distributeur",

    # ── CLIMATISATION ────────────────────────────────────────────────
    "Tropicalisé":                              "tropicalise",
    "Surface couverte clim":                    "surface_couverte",
    "Option(s) Climatiseur":                    "options",
    "Mode":                                     "mode",
    "Nombre de vitesses":                       "nombre_vitesses",
    "Accessoires Climatisation":                "accessoires",

    # ── ÉLECTROMÉNAGER ───────────────────────────────────────────────
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

    # ── MÉMOIRE ──────────────────────────────────────────────────────
    "Mémoire Ram":                              "memoire_ram",
    "RAM":                                      "memoire_ram",
    "Mémoire":                                  "memoire_ram",
    "Capacité de la mémoire":                   "memoire_ram",
    "Mémoire Vive de la Carte Graphique":       "memoire_gpu",
    "mémoire graphique":                        "memoire_gpu",
    "Fréquence mémoire max":                    "frequence_memoire",
    "Vitesse Mémoire":                          "frequence_memoire",
    "Fréquence mémoire":                        "frequence_memoire",

    # ── CARTE GRAPHIQUE ──────────────────────────────────────────────
    "Carte Graphique":                          "carte_graphique",
    "Chipset graphique":                        "carte_graphique",
    "Réf Carte Graphique":                      "ref_carte_graphique",
    "Réf Carte graphique":                      "ref_carte_graphique",

    # ── ÉCRAN ────────────────────────────────────────────────────────
    "Ecran":                                    "ecran",
    "Ecran intégré":                            "ecran",
    "Taille de l'écran":                        "taille_ecran",
    "Taille Ecran":                             "taille_ecran",
    "Résolution":                               "resolution",
    "Taux de Rafraîchissement":                 "taux_rafraichissement",
    "Luminosité":                               "luminosite",
    "Temps de réponse":                         "temps_reponse",
    "Rapport de contraste":                     "rapport_contraste",

    # ── CONNECTIVITÉ ─────────────────────────────────────────────────
    "Connectivité":                             "connectivite",
    "Connectivités":                            "connectivite",
    "Wifi":                                     "wifi",
    "Bluetooth":                                "bluetooth",
    "Ports":                                    "ports",
    "Nombre de ports":                          "nombre_ports",

    # ── SYSTÈME D'EXPLOITATION ───────────────────────────────────────
    "Système d'exploitation":                   "systeme_exploitation",
    "Système":                                  "systeme_exploitation",

    # ── PHYSIQUE ─────────────────────────────────────────────────────
    "Poids":                                    "poids",
    "Poids des produits":                       "poids",
    "Dimensions":                               "dimensions",
    "Dimension":                                "dimensions",

    # ── BATTERIE / AUTONOMIE ──────────────────────────────────────────
    "Autonomie":                                "autonomie",
    "Durée de vie maximale de la batterie":     "autonomie",
    "Capacité de batterie":                     "batterie",

    # ── DIVERS INFORMATIQUE ──────────────────────────────────────────
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


def _slugify(key: str) -> str:
    """Transforme une clé quelconque en snake_case ASCII."""
    key = unicodedata.normalize("NFD", key)
    key = "".join(c for c in key if unicodedata.category(c) != "Mn")
    key = key.lower()
    key = re.sub(r"[^a-z0-9]+", "_", key)
    key = key.strip("_")
    return key


# Index insensible à la casse construit une seule fois
_KEY_MAPPING_LOWER = {k.lower(): v for k, v in KEY_MAPPING.items()}


def normalize_specs(specs: dict) -> dict:
    """Normalise les clés d'un dict de specifications."""
    if not specs:
        return {}
    result = {}
    for raw_key, value in specs.items():
        if not raw_key or not value:
            continue
        key = raw_key.strip()
        # 1. Correspondance exacte
        canonical = KEY_MAPPING.get(key)
        # 2. Correspondance insensible à la casse (couvre variantes Mytek)
        if canonical is None:
            canonical = _KEY_MAPPING_LOWER.get(key.lower())
        # 3. Fallback : slugify générique
        if canonical is None:
            canonical = _slugify(key)
        result[canonical] = value
    return result
