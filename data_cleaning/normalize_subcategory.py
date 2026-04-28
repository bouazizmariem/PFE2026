# ── NORMALIZE_SUBCATEGORY.PY ──────────────────────────────────────────────────
# Normalisation des sous-catégories : doublons, suffixes parasites, valeurs vides


# ── VALEURS À TRAITER COMME None ─────────────────────────────────────────────
UNKNOWN_SUBCATEGORIES = {
    "none", "null", "",
    "divers",
    "accessoires divers",
    "electromenager",
    "informatique",
    "destockage",
    "composant informatique",
    "composants gamer",
    "electromenager cuisine",
    "electromenager specialise",
    "gros electromenager lavage",
    "climatisation chauffage",
    "chauffage et chauffe eau",
    "pack gaming",
    "pack electromenager",
    "pack encastrable",
    "pack electromenager",
    "gamer pc ps4",
    "setup gaming",
    "bagagerie",
}


# ── MAPPING CANONIQUE ─────────────────────────────────────────────────────────
# Clé   : forme brute telle qu'elle sort du scraper (après strip())
# Valeur: forme canonique normalisée

SUBCATEGORY_MAPPING = {

    # ── SUFFIXE "TUNISIE" PARASITE ────────────────────────────────────────────
    "Pc Portable Tunisie":                              "Pc Portable",
    "Pc Portables Pro Tunisie":                         "Pc Portable Pro",
    "Pc Portable Gamer Tunisie":                        "Pc Portable Gamer",
    "Pc Portable Asus":                                 "Pc Portable",
    "Pc Gamer Tunisie":                                 "Pc De Bureau Gamer",
    "Pc Bureau Tunisie":                                "Pc De Bureau",
    "Ordinateur De Bureau Gamer Tunisie":               "Pc De Bureau Gamer",
    "Blender Tunisie":                                  "Blender",
    "Hachoir Tunisie A Viande":                         "Hachoir",
    "Robot Multifonction Tunisie":                      "Robot Multifonction",
    "Cafetiere Tunisie":                                "Cafetiere",
    "Aspirateur Tunisie Vapeur":                        "Aspirateur",
    "Refrigerateur Tunisie":                            "Refrigerateur",
    "Ecran Pc Tunisie":                                 "Ecran Pc",
    "Ecran Gamer Tunisie":                              "Ecran Pc",
    "Hotte Aspirante Tunisie":                          "Hotte",
    "Climatiseur Tunisie Chaud Froid":                  "Climatiseur",
    "Boite Alimentation Pc Tunisie":                    "Bloc D Alimentation",

    # ── ÉCRANS ────────────────────────────────────────────────────────────────
    "Ecran":                                            "Ecran Pc",
    "Ecran Samsung":                                    "Ecran Pc",
    "Ecrans Gaming":                                    "Ecran Pc",
    "Afficheur Ecran":                                  "Ecran Pc",
    "Afficheur Pc Portable":                            "Ecran Pc",

    # ── PC PORTABLE ───────────────────────────────────────────────────────────
    "Ultrabook":                                        "Pc Portable",
    "Pc Portable Ia":                                   "Pc Portable",

    # ── PC DE BUREAU ──────────────────────────────────────────────────────────
    "Ordinateur De Bureau Gamer":                       "Pc De Bureau Gamer",
    "Unite Centrale":                                   "Pc De Bureau",

    # ── MAC ───────────────────────────────────────────────────────────────────
    "Macbook Pro":                                      "Mac",
    "Macbook Air":                                      "Mac",
    "Imac":                                             "Mac",

    # ── TABLETTE ──────────────────────────────────────────────────────────────
    "Ipad":                                             "Tablette",
    "Tablette Android":                                 "Tablette",

    # ── CLAVIER ───────────────────────────────────────────────────────────────
    "Clavier Spirit Of Gamer":                          "Clavier Gamer",
    "Clavier Pc Portable":                              "Clavier",

    # ── SOURIS ────────────────────────────────────────────────────────────────
    "Ensemble Clavier Et Souris":                       "Clavier Souris",

    # ── TAPIS SOURIS ──────────────────────────────────────────────────────────
    "Tapis Souris Spirit Of Gamer":                     "Tapis Souris",
    "Tapis De Souris Gamer":                            "Tapis Souris",

    # ── CASQUE ────────────────────────────────────────────────────────────────
    "Casque Ecouteurs":                                 "Casque",
    "Casque Gaming":                                    "Casque Gamer",
    "Micro Casque Gamer":                               "Casque Gamer",

    # ── MACHINE À LAVER ───────────────────────────────────────────────────────
    "Gros Electromenager Lavage":                       "Machine A Laver",

    # ── RÉFRIGÉRATEUR ─────────────────────────────────────────────────────────
    "Mini Bar":                                         "Mini Refrigerateur",
    "Mini Refrigerateur Mini Bar":                      "Mini Refrigerateur",
    "Refrigerateur Professionnel Solutions De Refrigeration Fiable":
                                                        "Refrigerateur",

    # ── FOUR ──────────────────────────────────────────────────────────────────
    "Four Star One":                                    "Four Electrique",
    "Four A Pizza":                                     "Four Electrique",
    "Mini Four Electrique":                             "Four Electrique",

    # ── HACHOIR ───────────────────────────────────────────────────────────────
    "Hachoir A Viande":                                 "Hachoir",

    # ── CAFETIÈRE ─────────────────────────────────────────────────────────────
    "Cafetieres":                                       "Cafetiere",
    "Cafe":                                             "Cafetiere",

    # ── MICRO-ONDES ───────────────────────────────────────────────────────────
    "Micro Ondes Encastrable":                          "Micro Onde",

    # ── BLOC D'ALIMENTATION ───────────────────────────────────────────────────
    "Alimentation":                                     "Bloc D Alimentation",
    "Boite Alimentation Pc":                            "Bloc D Alimentation",

    # ── BOITIER ───────────────────────────────────────────────────────────────
    "Boitier Spirit Of Gamer":                          "Boitier",
    "Boitier Disque Dur Externe":                       "Disque Dur Externe",
    "Etui Disque Dur":                                  "Disque Dur Externe",

    # ── SERVEUR ───────────────────────────────────────────────────────────────
    "Serveur Rack":                                     "Serveur",
    "Serveur Tour":                                     "Serveur",
    "Serveur Informatique":                             "Serveur",
    "Serveur De Stockage":                              "Serveur",
    "Serveur Rack":                                     "Serveur",
    "Station De Travail":                               "Serveur",

    # ── SAC À DOS ─────────────────────────────────────────────────────────────
    "Sac A Dos Scolaire":                               "Sac A Dos",
    "Sac A Dos Bange":                                  "Sac A Dos",

    # ── SACOCHE ───────────────────────────────────────────────────────────────
    "Sacoche Pc":                                       "Sacoche",
    "Sacs Sacoches":                                    "Sacoche",

    # ── HUB USB ───────────────────────────────────────────────────────────────
    "Hub Usb Lecteur Carte":                            "Hub Usb",
    "Lecteur De Carte":                                 "Hub Usb",
    "Hub Usb Lecteur Carte":                            "Hub Usb",

    # ── STOCKAGE ──────────────────────────────────────────────────────────────
    "Accessoires De Stockage":                          "Flash Disque",
    "Support De Stockage":                              "Flash Disque",

    # ── REFROIDISSEMENT ───────────────────────────────────────────────────────
    "Refroidisseur Ventilateur Boitier":                "Refroidisseur",
    "Refroidisseur Pc Bureau":                          "Refroidisseur",

    # ── LOGICIEL ──────────────────────────────────────────────────────────────
    "Antivirus Et Securite":                            "Logiciel Antivirus",
    "Logiciels Informatique":                           "Logiciel Antivirus",
    "Microsoft Office":                                 "Logiciel Microsoft",
    "Suite Bureautique":                                "Logiciel Microsoft",
    "Microsoft Windows":                                "Logiciel Microsoft",
    "Systeme D Exploitation":                           "Logiciel Microsoft",
    "Logiciel Microsoft":                               "Logiciel Microsoft",

    # ── MANETTE / CONTROLLER ──────────────────────────────────────────────────
    "Controller Manette De Jeux":                       "Manette Jeux Pc",
    "Manette Ps4":                                      "Manette Jeux Pc",
    "Manette Ps5":                                      "Manette Jeux Pc",
    "Manette Xbox":                                     "Manette Jeux Pc",
    "Manette Nintendo Switch":                          "Manette Jeux Pc",
    "Console De Jeux":                                  "Manette Jeux Pc",
    "Jeux Video":                                       "Manette Jeux Pc",

    # ── ACCESSOIRES ÉCRAN ─────────────────────────────────────────────────────
    "Support Ecran":                                    "Accessoires Ecran",
    "Filtre De Confidentialite Ecran Pc":               "Accessoires Ecran",

    # ── CASSEROLES / CUISINE ──────────────────────────────────────────────────
    "Faitouts Casseroles Cocottes":                     "Casseroles Poeles Faitouts",
    "Cocotte":                                          "Casseroles Poeles Faitouts",
    "Plats De Cuisson":                                 "Casseroles Poeles Faitouts",

    # ── RÉSEAU ────────────────────────────────────────────────────────────────
    "Cle Wifi Bluetooth":                               "Carte Reseau",
    "Reseau":                                           "Carte Reseau",

    # ── DIVERS INFORMATIQUE ───────────────────────────────────────────────────
    "Accessoires Ordinateurs":                          "Accessoires Et Peripheriques",
    "Accessoires Et Peripheriques":                     "Accessoires Et Peripheriques",
    "Dock Station":                                     "Station D Accueil",
    "Cd Dvd":                                           "Lecteur Cd Dvd",
    "Graveurs Et Lecteurs":                             "Lecteur Cd Dvd",
    "Lecteur Graveur":                                  "Lecteur Cd Dvd",

    # ── SANTÉ / BIEN-ÊTRE ─────────────────────────────────────────────────────
    "Entretien Soin":                                   "Beaute Masculine",
    "Sante Connectee Bien Etre Massage":                "Beaute Masculine",

    # ── CHAUFFAGE ─────────────────────────────────────────────────────────────
    "Radiateur A Bain D Huile":                         "Chauffage Electrique",
    "Radiateur Electrique":                             "Chauffage Electrique",
    "Convecteur":                                       "Chauffage Electrique",
    "Chauffage Soufflant":                              "Chauffage Electrique",

    # ── NETTOYAGE ─────────────────────────────────────────────────────────────
    "Nettoyage Entretien":                              "Nettoyeur",
    "Accessoires Nettoyeur":                            "Nettoyeur",
    "Balai Eponge":                                     "Nettoyeur",

    # ── REPASSAGE ─────────────────────────────────────────────────────────────
    "Table A Repasser":                                 "Table De Repassage",
    "Housse Table A Repasser":                          "Repassage Accessoires",

    # ── DIFFUSEUR ─────────────────────────────────────────────────────────────
    "Diffuseur D Arome":                                "Diffuseur",

    # ── WEBCAM / VISIO ────────────────────────────────────────────────────────
    "Visioconference":                                  "Accessoires Visioconference",
    "Haut Parleur De Conference":                       "Accessoires Visioconference",

    # ── MICROPHONE ────────────────────────────────────────────────────────────
    "Microphone Gaming":                                "Microphone Modulable",

    # ── FONTAINE ──────────────────────────────────────────────────────────────
    "Fontaine D Eau Fraiche":                           "Fontaine",
}


# ── FONCTION PRINCIPALE ───────────────────────────────────────────────────────

# Index insensible à la casse construit une seule fois
_SUBCATEGORY_MAPPING_LOWER = {k.lower(): v for k, v in SUBCATEGORY_MAPPING.items()}


def normalize_subcategory(subcategory: str) -> str | None:
    """
    Normalise une sous-catégorie brute vers sa forme canonique.

    Priorité :
      1. Valeur nulle / vide / parasite → None
      2. Correspondance exacte dans SUBCATEGORY_MAPPING
      3. Correspondance insensible à la casse
      4. Valeur strip()ée telle quelle (sous-catégorie inconnue mais valide)
    """
    if not subcategory:
        return None

    subcategory = subcategory.strip()

    # 1. Valeurs parasites
    if subcategory.lower() in UNKNOWN_SUBCATEGORIES:
        return None

    # 2. Correspondance exacte
    if subcategory in SUBCATEGORY_MAPPING:
        return SUBCATEGORY_MAPPING[subcategory]

    # 3. Correspondance insensible à la casse
    sub_lower = subcategory.lower()
    if sub_lower in _SUBCATEGORY_MAPPING_LOWER:
        return _SUBCATEGORY_MAPPING_LOWER[sub_lower]

    # 4. Fallback : valeur nettoyée telle quelle
    return subcategory