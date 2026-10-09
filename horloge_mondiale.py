#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Horloge mondiale - F4GOP
========================
- Onglet « Villes »  : heure UTC, heure locale et grille de villes
                       (☀ jour, ◐ grayline / crépuscule, ☾ nuit, selon le vrai soleil)
- Onglet « Carte »   : carte du monde jour/nuit avec grayline, QTH, villes ;
                       survol = locator, distance, azimut, hauteur du soleil
- « Compact »        : petite bande UTC toujours au premier plan, déplaçable
                       (double-clic ou clic droit pour revenir)
- ⚙ Réglages        : indicatif, locator, démarrage automatique avec Windows

Clic droit sur une ville : la supprimer. Les réglages sont enregistrés dans
horloge_mondiale.json (dossier utilisateur).

Prérequis : Python 3.9+ (tzdata est installé automatiquement sous Windows).
Astuce : renommer le fichier en .pyw pour ne plus avoir la fenêtre console.
"""

import base64
import json
import math
import os
import re
import sys
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
import zlib
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox
from datetime import datetime, timezone, timedelta

try:
    from zoneinfo import ZoneInfo, available_timezones, ZoneInfoNotFoundError
except ImportError:  # Python < 3.9
    raise SystemExit("Python 3.9 ou plus récent est nécessaire.")

APP = "Horloge mondiale"
CONFIG = os.path.join(os.path.expanduser("~"), "horloge_mondiale.json")
GELE = getattr(sys, "frozen", False)  # True dans l'exécutable PyInstaller

VILLES_DEFAUT = [
    {"nom": "France", "tz": "Europe/Paris", "lat": 48.86, "lon": 2.35},
    {"nom": "Royaume-Uni", "tz": "Europe/London", "lat": 51.51, "lon": -0.13},
    {"nom": "USA Est", "tz": "America/New_York", "lat": 40.71, "lon": -74.01},
    {"nom": "USA Ouest", "tz": "America/Los_Angeles", "lat": 34.05, "lon": -118.24},
    {"nom": "Brésil", "tz": "America/Sao_Paulo", "lat": -23.55, "lon": -46.63},
    {"nom": "Alaska", "tz": "America/Anchorage", "lat": 61.22, "lon": -149.90},
    {"nom": "Hawaï", "tz": "Pacific/Honolulu", "lat": 21.31, "lon": -157.86},
    {"nom": "Russie (Moscou)", "tz": "Europe/Moscow", "lat": 55.76, "lon": 37.62},
    {"nom": "Émirats", "tz": "Asia/Dubai", "lat": 25.20, "lon": 55.27},
    {"nom": "Inde", "tz": "Asia/Kolkata", "lat": 28.61, "lon": 77.21},
    {"nom": "Chine", "tz": "Asia/Shanghai", "lat": 39.90, "lon": 116.40},
    {"nom": "Japon", "tz": "Asia/Tokyo", "lat": 35.68, "lon": 139.69},
    {"nom": "Australie Est", "tz": "Australia/Sydney", "lat": -33.87, "lon": 151.21},
    {"nom": "Nouvelle-Zélande", "tz": "Pacific/Auckland", "lat": -41.29, "lon": 174.78},
    {"nom": "Afrique du Sud", "tz": "Africa/Johannesburg", "lat": -26.20, "lon": 28.05},
    {"nom": "La Réunion", "tz": "Indian/Reunion", "lat": -20.88, "lon": 55.45},
]

# Anciens noms de villes (version précédente) -> noms de pays
ANCIENS_NOMS = {
    "Paris": "France", "Londres": "Royaume-Uni", "New York": "USA Est",
    "Los Angeles": "USA Ouest", "São Paulo": "Brésil", "Anchorage": "Alaska",
    "Honolulu": "Hawaï", "Moscou": "Russie (Moscou)", "Dubaï": "Émirats",
    "New Delhi": "Inde", "Pékin": "Chine", "Tokyo": "Japon",
    "Sydney": "Australie Est", "Wellington": "Nouvelle-Zélande",
    "Johannesburg": "Afrique du Sud", "Réunion": "La Réunion",
}

PAYS_FR = {
    "FR": "France", "GB": "Royaume-Uni", "IE": "Irlande", "BE": "Belgique",
    "NL": "Pays-Bas", "LU": "Luxembourg", "DE": "Allemagne", "CH": "Suisse",
    "AT": "Autriche", "IT": "Italie", "ES": "Espagne", "PT": "Portugal",
    "MC": "Monaco", "AD": "Andorre", "DK": "Danemark", "NO": "Norvège",
    "SE": "Suède", "FI": "Finlande", "IS": "Islande", "PL": "Pologne",
    "CZ": "Tchéquie", "SK": "Slovaquie", "HU": "Hongrie", "RO": "Roumanie",
    "BG": "Bulgarie", "GR": "Grèce", "HR": "Croatie", "SI": "Slovénie",
    "RS": "Serbie", "BA": "Bosnie-Herzégovine", "ME": "Monténégro",
    "MK": "Macédoine du Nord", "AL": "Albanie", "UA": "Ukraine",
    "BY": "Biélorussie", "MD": "Moldavie", "LT": "Lituanie", "LV": "Lettonie",
    "EE": "Estonie", "RU": "Russie", "TR": "Turquie", "CY": "Chypre",
    "MT": "Malte", "US": "États-Unis", "CA": "Canada", "MX": "Mexique",
    "CU": "Cuba", "BR": "Brésil", "AR": "Argentine", "CL": "Chili",
    "PE": "Pérou", "CO": "Colombie", "VE": "Venezuela", "UY": "Uruguay",
    "PY": "Paraguay", "BO": "Bolivie", "EC": "Équateur", "GF": "Guyane",
    "GP": "Guadeloupe", "MQ": "Martinique", "PM": "Saint-Pierre-et-Miquelon",
    "RE": "La Réunion", "YT": "Mayotte", "NC": "Nouvelle-Calédonie",
    "PF": "Polynésie française", "WF": "Wallis-et-Futuna", "MA": "Maroc",
    "DZ": "Algérie", "TN": "Tunisie", "LY": "Libye", "EG": "Égypte",
    "SN": "Sénégal", "CI": "Côte d'Ivoire", "CM": "Cameroun", "NG": "Nigeria",
    "KE": "Kenya", "ET": "Éthiopie", "ZA": "Afrique du Sud", "MG": "Madagascar",
    "MU": "Maurice", "CD": "RD Congo", "CG": "Congo", "GA": "Gabon",
    "ML": "Mali", "NE": "Niger", "TD": "Tchad", "SA": "Arabie saoudite",
    "AE": "Émirats arabes unis", "QA": "Qatar", "KW": "Koweït", "IL": "Israël",
    "LB": "Liban", "JO": "Jordanie", "SY": "Syrie", "IQ": "Irak", "IR": "Iran",
    "AF": "Afghanistan", "PK": "Pakistan", "IN": "Inde", "NP": "Népal",
    "BD": "Bangladesh", "LK": "Sri Lanka", "CN": "Chine", "HK": "Hong Kong",
    "TW": "Taïwan", "JP": "Japon", "KR": "Corée du Sud", "KP": "Corée du Nord",
    "MN": "Mongolie", "TH": "Thaïlande", "VN": "Viêt Nam", "KH": "Cambodge",
    "LA": "Laos", "MY": "Malaisie", "SG": "Singapour", "ID": "Indonésie",
    "PH": "Philippines", "AU": "Australie", "NZ": "Nouvelle-Zélande",
    "FJ": "Fidji", "KZ": "Kazakhstan", "UZ": "Ouzbékistan", "GE": "Géorgie",
    "AM": "Arménie", "AZ": "Azerbaïdjan", "GL": "Groenland", "AQ": "Antarctique",
}

CONFIG_DEFAUT = {
    "villes": VILLES_DEFAUT,
    "indicatif": "F4GOP",
    "locator": "IN98QR",
    "vue": "villes",
    "secondes": False,
    "premier_plan": False,
    "compact_pos": None,
}

JOURS = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
MOIS = ["jan", "fév", "mar", "avr", "mai", "juin",
        "juil", "août", "sep", "oct", "nov", "déc"]

# Couleurs (thème sombre « tableau de bord »)
FOND = "#0d1117"
PANNEAU = "#151b23"
PANNEAU2 = "#1c2430"
SURVOL = "#243040"
BORD = "#26313d"
SEL = "#24405a"
TEXTE = "#e6edf3"
TEXTE_DIM = "#7d8b99"
UTC_COUL = "#4fc3f7"
ACCENT = "#ffb547"
CORAIL = "#ff8a5c"
LUNE = "#9aa8ff"
QTH_COUL = "#ff6b6b"
CARTE_JOUR = PANNEAU  # compatibilité
CARTE_GRIS = PANNEAU
CARTE_NUIT = PANNEAU

COLONNES = 4
CARTE_L, CARTE_H = 720, 360  # pixels de la carte (0,5° par pixel)

# Masque terre/mer 720 x 360 (0,5°), 1 bit par pixel, zlib + base64
MASQUE_TERRE = (
    "eNrtnU9sHcd5wGffPnJeLFrLVgZMwwyXqAMkhwJiGiSRAYX7EgdIgAT1sYcGFY0USHoKC/cgF7R2GRpRDknoW4LAyNMtySUV"
    "eqmKGOaqcqEEQSqhfxIBDaJ1lUIq6pgr0zaX4nImM7Oz+3Z2598+kYcEnINIvrf729lvvu+b7/tmdgXAcTtux+24/f601S2M"
    "00PkeRjjUUR/2SG/4eTQwP425eXg44E3or8dGjjErMHbu/QHwnnuZK2DTk7SY7iPt/Fe5uKy7WDUPMiJq9/sycHV29sBRmMw"
    "3mpKuveP0y/ucvY56wF28MEoIAoRjsn4tfJL979iQK7ixn9/szz8tvX4rmBMBLwf1fqMrxRfwXd3/ZbEv7Jlx4Ux7TRVB1gj"
    "8xvvocxtn4Ees0Pj+RN4iwjWq4HzYfHd1IFUtUM7ecDN6C0i4o0aGGecDD6cr8o6MzBjT6WDeZCBHWLQfo28+3X+/WwWTGgi"
    "AEzT84NdMvz1Tl8qb0h6355RGu723DTouZlPnVBdzm9Vh8R1YMwtJch7JuOL3/HAb7PP5YBogPveP1RktCg5+qM4Ksjr5IhI"
    "T+5/BG9kn0tBDl4tjLFCS06E5YfMoi6zawRbqisQFb4fpXslqhrE/LLEB8R195Xwrly/pPLL5IjZM3vcmseDKBvtontP1Q8g"
    "w78idxhzTUUt5dy+STerbpO0+/wGhirzI5fuu6+GyVpPID9AktHmHq6Q2Hf5EJ9VOTm0Cn7kpOHGzgGqTwF3JePiF86/OIL4"
    "xcyhYzOtUGd89+43sifQF+Fd9Ol6n397s33wBTpgX+0FNa0nY7So0oxNjHIXLXl39wq3Xp63JCeH/+J5AtmtvGJDGoiQLoC1"
    "L3u7ePfL9JMd0YkKx1LyK/h/6+QhGB/KBrhyuSvkmgg4uVvSThSn7Enmo3NUegvefp1c07+COZ4+6b2R7lAy+k/y93wxQFmN"
    "PP03K6VvcvANOkdUjf+OhKil9DYvYjbII3wb/zP55Mni2G/VpPBNnJVW4ZJx2cHtNjZT1i0Atv/nDO3sm3MXAFwnjp9ofXCu"
    "6TamiaZwF3fZxSMsa8DZLs4Ix0KKPXw7Pff46/DeB0LmCgrleDDu8yfIn7douEfOi/G3sLxtYBQDwQ/j6/mZgQfvTuWOj5ru"
    "hkl3xP8eLi2EeXB9hFUta5DTjQWw4L11OnWu4ZfJCDNyzRnMhsVZKfwZ+Rle31aSiTyc+p/3zuP//48Q+xm8SmXQ32KB47h9"
    "kp+VFmK6dltNjscOrWghjbW2sh7TxRP8vqo2xc+Ki5+eGoy3I2GSZmQqFWqoWeGg62bCjt3EcXHUg0AN3sKp57Y/fjsm4ieR"
    "IOS3tVRGnkyuaXASG9sIXwrbn+68Rd0TsTKXyHGfAJ/G1dSUE4cJQjM5wg1hFO3nAG7hq8UYFELISnJCfzeDMXg/8CUGOqJR"
    "HYVtFpox4sImgktIt1eNXPSKOI9Wzc96LrO8oLA/j9s3uV5sUImxoUjIKA180GO9DQvPVU6nxI1cxFaNnLwgEXQyDeZAuMz6"
    "nImpUe5ZkyXCQMzhwNfZ0KXCRInTwI6MgBjaV9cbbv7KSdmXiWgniW/RX65RnlT6mxj0W+TAivzGGrdb2udtQfXTsTY4TXJs"
    "JkcJn2d7lCocn7DrFUP3wbizNMA1PhU+TcQdOm3yHovA4Hii6tM+741MY5gD7zeDcobNU+7jx9EF6XM7kgrY6BqcRgqWx3N3"
    "GtejcEYml4OtaO40m9m1pjcY5qCaKh75y0xUkZyJ9D2/FRn5d4ikDB0mo743njZ36rFyQfYwasRcT0UkWMDRQCsMeptwbFyQ"
    "RSrfFuzHbUxT5Frs8i/pxcxGYxwkLczTf38pZFIubpaPaLFhDn99PjR4C5LDVeecYf++IBi90yLTFOZ8GAdG3zme7J2Ep3f1"
    "m3quJQ2avuYBCEwDWAtAH+VnnmvE2EKgQVNyAPYu68kxcwjVvf5ZFQuO49VCCQXleIbcQvgS8E0DOCaXE75bP6co9dQF7WTn"
    "AXiejKFuAGfFPgtRSimOFtlLSWZyNtZb9r9Sz1vFz2V20xP6zMR5VlCNwOgyivQON6ttDmySD+qJvHcfR2YP+ma9z/V0fhx+"
    "Bc10G6ZcRNr2b2VWJS1aMpX3m2Q/sSFTRT1fJvft/J1aYShmSSQTdssI1NTnVVlC3wh274h+/4552qa+rV2HcFpJxzXh62xk"
    "R470fab6cU6QVd9CNfBmLSOutbPiUVfjR5UjrCFLawXiqWDJExTocYug6xvyCpUrZEo5quouRfuMBXlGUZMRPOR+DoJMqNhY"
    "NEWB1BH6vJuD8L2OYs4HygpVPZ8j9vR5lS9UkWdsyPigx8JRoVpRNGXcn53Ur3aUFv6lZgGLn55D5Tz4Ias+4+/LyelZZUZB"
    "K5QW5CxvlvOKaDgJtpQz7ByILMjX47b/dtnpyrGMZnoW0si99sww2mCxm6ucuxcWLcjZTIuM4NV2SURIqPzXFXXRZuQvjh+a"
    "g3R+VBtNRmYeC3LcIufgROoxslzQJNLEoDvZoTf7HF1/U5KJl/majT4nkj6vYHIBsKYgpwBEFuS8fUPkTH+dzAhYEeqqq8Qm"
    "cgwS+Ab6c4UF3qDkxELOaavsTdRtxf1ppnJHmzSiSi36LCH3yYS/ripDoAWaBlqQ0aW2ndBQIr7gqSLcBQ05VCjdsLBt+mt0"
    "1lW5uaBKTIAs+636HLekQWMxJzp1UZWiBFFtQVkdmwtrM31GptqyBr4wpZDGEMbAtSG3l0SIDGfnwbzCHeUZSb4+E2t2EyhX"
    "qvzEvZ3T3u89kAuaJIxhNAl5AMIiQ5yVFwIjmCxizSKeekVw4FSGKff6MOlhlTRcjZzBzEVGdu6BJbnXh3GYR8Bo3rl0eFG5"
    "iC8lg/3vmLZXYNk2E7/61FGUNp46p16N9VV+n18115Ife0GzPq8mO2MZye07Hiys2JAVo5vSYoiCDJ4dapbS1aoB+ee5ipyo"
    "FjRFCeZKMukbVLgk3c4Z53q9bCOzT4CR5yn6rN0RccdETrEmDjWT713MtJYvbT/Qk/+WHvPfWX9N662kYb9hhw9LNuO/k6yI"
    "13z3j+kuqK7kee7mFloutDaT7ePGZhcbOX8+LDRuufF5rz770uRuvSt52S/0YlnjYPH/4WLBpl1s1e064WRfpxopS1Y6kt3N"
    "guyZyOn7g1YVUMt2NhTkZpkwbZYxkWnPWjElATjUkDNCfhuM2os+2na1UMyeJnzCOfnjgRMtw07khPuMPzKQEWwkb/mSaatl"
    "WBjTQBNMIioatqetLvwVA3mOr9sNNKE1gtyaBUMx7dAa+HIH0CY31mxi494vj5FxNKtJ6Fw+ZLD0IrTUGhu311Gys5lEGvIG"
    "N42gXA0kLh0MzWQq58VMtChxUr3G++yH5fYMFJm32LmETOLVBbVD4mQiZ495RgpW1bzEPufAj5suSZTGG3yq7LPFt5AuhNls"
    "Y6TkqL741A5smQt9p9DyjEo7U9HiRnZGyBFc0RQoAu7pQ/qD7iCcV5AjUaI0SwJubkGmC7N07k3PW+0XxSzdcJCmjBDwmDKg"
    "Dp+uzlqRQ7xNVHXB+/cz6kKQz+eQgO+FTavyvn4I2Ta7hicVyR73mgG3xExe3m/PpchUFoMVOWPk3KrPoE3uNUaQkpNqxwi/"
    "jAXZL8kzKt3I3WpzJt0q5bNAftXCviHC+uIV4oUDQo6KOTJSlmOakm6aktskI+5y+ewb25GddlgCmzvGkhrZY+R7dsYSA52v"
    "w3f4AbBG/msbstfqcyMFfBeBFvmHkY2gi2pCX9nn/aQks0X5gArnOWBl4ZFeGgdR+TGtMhXkRSsydXaxpuiNgECGVBp/smJD"
    "Jg7aiTSLCznPKh1Gdl1KHlh1moSi3oJmBBHgKRIbwUcY+VGrPpOgLUTgA4q4jq4k5DXyNBPKI1Zy9gg5vP8bzQIQJ6NCh4g3"
    "6rlW0piKQShuzIJy8lrEyGSS6Pcjq06nKQ6EtB7K9lMQMtWgKboaP+jN2in0E41g25WTV9k+IKrLs2DJinzSb6RLrjxj/XBS"
    "7VlyMysy9BslHwWZ+U6XkT07cs9rpqWKjJVtE6LkxYGVG+UjlqpXNOMamXV8CLqQM1Gh07BNTkr8itWkUmlZKtQ3mju4qnae"
    "7YBY7ELOGzGqNMt24zUarNkZSmUZNZ+UCCZe91Z0nwu0fugKSgsAgbRSSMleKi4HG2uCjZn2nDQXXlsGkd+1z7GiTCUE18sL"
    "AxAktmRPTxa2BfgLsk1IhnpxoiALn3s32MqFY6cdgbRU5kvV2b0DTlEyOAyy8OlTGQukP2nXZ6wliwH2qSwOSSq7DrqQRc/Y"
    "96VFZPcBoLGMjTRWqijg1/I+N1wxGhLywOmZycOK3FhyCxVk0uc3/thdv29vgvggk1q3KP5+GHn46hU731GS95FUGqKa98KX"
    "PbyergzSzJ6M5WRRRk4Qe3iDXO3mBXvdwCiR2WDTYPcI+TIAV8jN9G3JYv+ggpyC2xtXHj3/Ihlax1YaokxdOZk45+n1K/3+"
    "VyyeUHblVXZHXqmkSuG8ws6KnaGVe27prmJnACW/zPQ9MXk8V1GyVqwQUfJLTHdS114awhAqyDwM/ayHswv9ycihvCLMC+ED"
    "kjXP9ay1TkJu9Tn4WknOjWoXysmBvM+wypZzY2LYjQxGtwCY6REbXQbg01azVZPsK8gumqV7CuaRB0yxf0cy8RkZXeu6QOP/"
    "oU1U0NTnQLNaQN1A3/3J0CBoeXCoIbvr7N6cd9SbOBoxi4jxFSvLpPGp+4xqi12bnEvIet8wsHRJueSCcnIvAjMdpivR13Hy"
    "V6XnzKx0I6dSacjGv4eG81aVNd5uStRcToY4OtmFHEuMPpIamofrCw+O0dnJyatGMpiQnEqrAMOHJseOhBz4CPixmRxIyaUr"
    "kZUcaGm+2CHZt3McUjK8J3XpkW+RYkEdGYRtaTh0caUiOxZqF8siGcl7Meh3GU8LI61AQnWfUyBZ6/fYCm3zXvrtxWIp2Sk/"
    "UpDHvmDOYgijdp81ZJtiki+LO0N+MclOKL9GtpuvohYZ0afGFcfn9jk9bttPJiWH6omsEzlqznaucsOYiixJgXK6aq1TpU+V"
    "H0Y6cq4gOwoPFhsHUE72+FYNrJzdEoMyj8lZ25ugYuVA7mYSo68rtS6Vkdt99tV70RRkBKRkpIx8rMmZJdm33ntSHht3JWNb"
    "ciRRAXLDuZp8yZIsU65EsjTq2e54KslIRo61sWtsR85tyac7kINOffYfluwchjTU5EhLTiYjAxUZdiCHUlsNFbbQmZxJ7gTp"
    "cwRLcioh54dCvtydHNuRI4neZkdD9hRbTp2uZJneJipy/FBkqDqVPW1l5+tC6QThKU51+M4kG8+vIiNVIE9uaNs8W/UKsmwb"
    "dKbIplHxCKnFPEgfqGyrgauoi7vsuZiR1dxNyPcl2YjqcHorzuM2ZMcygG9qTlZWZg6X/HxpR3OGAkfelezYvDHUtYt3WoNT"
    "kKcMOWw+MRkayJ3lDELuVdzv6Mnd37Lqf4+fnenJUWdymQrrFprch3oxrBdr+/wQZHhkZDfSJkDJBMihDTmfpLN8x9gvNYdM"
    "TUYOGNnRWcKJSZSO7RgDxXKThnwwEbkQs26InpxMGkWZ2Is0xS93Aq8xlnasIZ94GDLSJ0CTkx2tIJ+0qa6oJJnr+xxNTs70"
    "acrkZK06E/Lk0nAMKexhvre73v7iyMjBIb4Q/PDkbCKbdeNDE5FPP4TWGdwhAkcljfz3j0z39B6NRn/wgeHhuonb6V8clTTA"
    "Xx0VePrGUekz+KdYDFwPrz1+YONsJ2mPxOC4Hbfj9gfcekfEHR6L1jIMfqg2dWQueuWowKd+clTkXx+ZmNMjUw1Lcve4BOoS"
    "FWHFO0xYfQ6+bdnlke7bZ6uUgK1YbdL/PsHDdrmNKXkunpkr11Ey61VYoK9OsyW+dLb9vJvVo82avXKw3BngYvmzY/q2HClv"
    "JiyX1SSvlnnVrM3BTcU3Z53xO74kr3+5ZXL6L8jSY7YjO6j+U473Kd/0q2t/Kk28I+FVR6Hy7cRaMTd2jc2yZaH8ifXGOwBU"
    "L2vWGFkoHDC/2n7v4LrupdiStsj+vYDFXFM2Vhdxp06XezO+ECATWf+G6bZSxOAZtogT6p6mnIQc5nh0C9y6dxrv1D7tBG55"
    "nDm2vfRp9gB33jigE7klZvc1sFR/y1T9gLALWVBox0nAXdLN1Vr3asvoXhfwnthh/ulrcPzM5KSakcnAinEIJxazc6P57Z36"
    "El43sED+GNR963cD127Wy555tv06ugmNhJ7bHw/8ru7CXbtcd0i+8o1j9IUEncH4R5oR2kiLJ6C9zO4dynJJyrq1Fxfv0/B1"
    "77A1CsNLZSfXKrqwI7luJ57ia6h5H6ydCXqKW2LPz4ZdpRGbFDaaTJsFVwc1ptRdm+viUL34jy5QhHhyrVN632gCSYidVjnf"
    "JJiQXGo0xIffkglmT1tZM5Nw8BG15GgEctyO23GzaL8DjeXU+A=="
)

ICONE_PNG = (
    "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"
)



# ---------------------------------------------------------------- propagation
URL_HAMQSL = "https://www.hamqsl.com/solarxml.php"
URL_KC2G_STATIONS = "https://prop.kc2g.com/api/stations.json"
URL_KC2G_MUF = "https://prop.kc2g.com/renders/current/mufd-normal-now.geojson"
URL_OVATION = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"
PERIODE_DONNEES = 15 * 60  # secondes

# Couleur selon la MUF (MHz) : seuil haut exclu
ECHELLE_MUF = [(7, "#5b6cff"), (10, "#3fa0ff"), (14, "#2fd0d0"), (18, "#3fd46b"),
               (21, "#c8e04a"), (24, "#ffd23f"), (28, "#ff9f3f"), (35, "#ff5c5c"),
               (999, "#ff4fd8")]


def couleur_muf(v):
    for lim, c in ECHELLE_MUF:
        if v < lim:
            return c
    return ECHELLE_MUF[-1][1]


def telecharger(url):
    req = urllib.request.Request(url, headers={"User-Agent": "HorlogeMondiale-F4GOP/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def lire_hamqsl(data):
    sd = ET.fromstring(data).find("solardata")

    def t(tag):
        e = sd.find(tag)
        return (e.text or "").strip() if e is not None else ""

    res = {k: t(k) for k in ("updated", "solarflux", "aindex", "kindex", "xray",
                             "sunspots", "solarwind", "magneticfield", "geomagfield",
                             "signalnoise", "aurora", "latdegree")}
    res["bandes"] = {(b.get("name"), b.get("time")): (b.text or "").strip()
                     for b in sd.iter("band")}
    res["vhf"] = [(p.get("name"), p.get("location"), (p.text or "").strip())
                  for p in sd.iter("phenomenon")]
    return res


def lire_stations(data):
    maintenant = datetime.now(timezone.utc)
    out = []
    for e in json.loads(data):
        try:
            st = e["station"]
            muf = e.get("mufd")
            if muf is None:
                continue
            cs = e.get("cs")
            if cs is not None and 0 <= cs < 10:
                continue
            t = datetime.fromisoformat(e["time"].replace("Z", "")[:19]).replace(tzinfo=timezone.utc)
            age = (maintenant - t).total_seconds() / 60
            if age > 180:  # données trop anciennes
                continue
            lon = float(st["longitude"])
            if lon > 180:
                lon -= 360
            out.append({"nom": st.get("name", "?"), "lat": float(st["latitude"]), "lon": lon,
                        "muf": float(muf), "fof2": e.get("fof2"), "age": age})
        except (KeyError, ValueError, TypeError):
            continue
    return out


def lire_contours(data):
    out = []
    for f in json.loads(data).get("features", []):
        g = f.get("geometry") or {}
        niveau = (f.get("properties") or {}).get("level-value")
        if niveau is None:
            continue
        lignes = [g.get("coordinates", [])] if g.get("type") == "LineString" else \
            g.get("coordinates", []) if g.get("type") == "MultiLineString" else []
        for l in lignes:
            if len(l) > 1:
                out.append((float(niveau), [(float(p[0]), float(p[1])) for p in l]))
    return out


def lire_ovation(data):
    grille = [[0] * 360 for _ in range(181)]
    for lon, lat, v in json.loads(data).get("coordinates", []):
        grille[int(lat) + 90][int(lon) % 360] = v
    return grille


def recuperer_donnees():
    """Télécharge toutes les sources (appelé dans un thread)."""
    res = {"erreurs": [], "heure": datetime.now(timezone.utc)}
    for cle, url, lecteur in (("solaire", URL_HAMQSL, lire_hamqsl),
                              ("stations", URL_KC2G_STATIONS, lire_stations),
                              ("contours", URL_KC2G_MUF, lire_contours),
                              ("aurore", URL_OVATION, lire_ovation)):
        try:
            res[cle] = lecteur(telecharger(url))
        except Exception:
            res["erreurs"].append(cle)
    return res


FR_BANDES = {"Good": ("Bon", "#1f7a4d"), "Fair": ("Moyen", "#8f6514"), "Poor": ("Mauvais", "#7f2d2d")}
FR_GEOMAG = {"VR QUIET": "très calme", "QUIET": "calme", "UNSETTLD": "instable",
             "ACTIVE": "actif", "MIN STORM": "orage mineur", "MAJ STORM": "orage majeur",
             "SEV STORM": "orage sévère", "EXT STORM": "orage extrême"}
VHF_NOMS = {("vhf-aurora", "northern_hemi"): "Aurore", ("E-Skip", "europe"): "Es EU 2m",
            ("E-Skip", "europe_4m"): "Es EU 4m", ("E-Skip", "europe_6m"): "Es EU 6m",
            ("E-Skip", "north_america"): "Es NA"}
VERT, ORANGE, ROUGE = "#5fd38a", "#ffb347", "#ff6b6b"


def couleur_indice(cle, val):
    try:
        if cle == "kindex":
            v = float(val)
            return VERT if v <= 2 else ORANGE if v <= 4 else ROUGE
        if cle == "aindex":
            v = float(val)
            return VERT if v < 10 else ORANGE if v < 30 else ROUGE
        if cle == "solarflux":
            v = float(val)
            return VERT if v >= 120 else ORANGE if v >= 80 else ROUGE
        if cle == "magneticfield":
            v = float(val)
            return VERT if v > -2 else ORANGE if v > -8 else ROUGE
        if cle == "solarwind":
            v = float(val)
            return VERT if v < 450 else ORANGE if v < 600 else ROUGE
        if cle == "xray":
            return {"A": VERT, "B": VERT, "C": ORANGE, "M": ROUGE, "X": ROUGE}.get(val[:1], TEXTE)
    except ValueError:
        pass
    return TEXTE


# ---------------------------------------------------------------- utilitaires
def fmt_date(dt):
    return f"{JOURS[dt.weekday()]} {dt.day} {MOIS[dt.month - 1]}"


def fmt_offset(dt):
    minutes = int(dt.utcoffset().total_seconds() // 60)
    signe = "+" if minutes >= 0 else "-"
    h, m = divmod(abs(minutes), 60)
    return f"UTC{signe}{h}" + (f":{m:02d}" if m else "")


def fmt_latlon(lat, lon):
    return (f"{abs(lat):.1f}°{'N' if lat >= 0 else 'S'} "
            f"{abs(lon):.1f}°{'E' if lon >= 0 else 'O'}")


def fmt_km(km):
    return f"{km:,.0f}".replace(",", " ") + " km"


LOCATOR_RE = re.compile(r"^[A-R]{2}[0-9]{2}([A-X]{2})?$", re.I)


def locator_vers_latlon(loc):
    loc = loc.strip().upper()
    if not LOCATOR_RE.match(loc):
        raise ValueError(loc)
    lon = (ord(loc[0]) - 65) * 20 - 180 + int(loc[2]) * 2
    lat = (ord(loc[1]) - 65) * 10 - 90 + int(loc[3])
    w, h = 2.0, 1.0
    if len(loc) == 6:
        lon += (ord(loc[4]) - 65) * 5 / 60
        lat += (ord(loc[5]) - 65) * 2.5 / 60
        w, h = 5 / 60, 2.5 / 60
    return lat + h / 2, lon + w / 2


def latlon_vers_locator(lat, lon):
    lon = min(max(lon + 180, 0), 359.9999)
    lat = min(max(lat + 90, 0), 179.9999)
    return (chr(65 + int(lon // 20)) + chr(65 + int(lat // 10)) +
            str(int((lon % 20) // 2)) + str(int(lat % 10)) +
            chr(97 + int((lon % 2) * 12)) + chr(97 + int((lat % 1) * 24)))


def distance_azimut(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    c = math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dl)
    d = math.acos(max(-1.0, min(1.0, c))) * 6371.0
    az = math.degrees(math.atan2(math.sin(dl) * math.cos(p2),
                                 math.cos(p1) * math.sin(p2) -
                                 math.sin(p1) * math.cos(p2) * math.cos(dl)))
    return d, az % 360


# ---------------------------------------------------------------- soleil
def soleil(dt_utc):
    """Déclinaison (radians) et longitude du point subsolaire (degrés)."""
    n = dt_utc.timestamp() / 86400.0 + 2440587.5 - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)
    decl = math.asin(math.sin(eps) * math.sin(lam))
    ra = math.degrees(math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam)))
    gmst = (280.46061837 + 360.98564736629 * n) % 360
    sublon = (ra - gmst + 180) % 360 - 180
    return decl, sublon


def hauteur_soleil(lat, lon, sol):
    decl, sublon = sol
    p = math.radians(lat)
    s = (math.sin(p) * math.sin(decl) +
         math.cos(p) * math.cos(decl) * math.cos(math.radians(lon - sublon)))
    return math.degrees(math.asin(max(-1.0, min(1.0, s))))


def etat_soleil(h):
    if h > 0:
        return "jour"
    if h > -6:
        return "grayline"
    if h > -12:
        return "crépuscule"
    return "nuit"


def lever_coucher(lat, lon, minuit_local):
    """Heures de lever / coucher (datetime UTC ou None) pour la journée locale."""
    debut = minuit_local.astimezone(timezone.utc)
    seuil = -0.833
    lever = coucher = None
    t0, h0 = debut, hauteur_soleil(lat, lon, soleil(debut)) - seuil
    for i in range(1, 721):
        t1 = debut + timedelta(minutes=2 * i)
        h1 = hauteur_soleil(lat, lon, soleil(t1)) - seuil
        if h0 < 0 <= h1 and lever is None:
            lever = t0 + (t1 - t0) * (-h0 / (h1 - h0))
        elif h0 >= 0 > h1 and coucher is None:
            coucher = t0 + (t1 - t0) * (h0 / (h0 - h1))
        t0, h0 = t1, h1
    return lever, coucher


# ---------------------------------------------------------------- données
def coords_fuseaux():
    """Coordonnées de la ville principale de chaque fuseau (zone.tab)."""
    textes, iso = [], ""
    try:
        import importlib.resources as res
        base = res.files("tzdata").joinpath("zoneinfo")
        try:
            iso = base.joinpath("iso3166.tab").read_text(encoding="utf-8")
        except Exception:
            pass
        for nom in ("zone1970.tab", "zone.tab"):
            try:
                textes.append(base.joinpath(nom).read_text(encoding="utf-8"))
            except Exception:
                pass
    except Exception:
        pass
    if not textes:
        for nom in ("zone1970.tab", "zone.tab"):
            try:
                with open(os.path.join("/usr/share/zoneinfo", nom), encoding="utf-8") as f:
                    textes.append(f.read())
            except Exception:
                pass
        try:
            with open("/usr/share/zoneinfo/iso3166.tab", encoding="utf-8") as f:
                iso = f.read()
        except Exception:
            pass

    def conv(s):
        signe = -1 if s[0] == "-" else 1
        s = s[1:]
        if len(s) in (4, 5):  # DDMM / DDDMM
            d, m, sec = s[:-2], s[-2:], "0"
        else:  # DDMMSS / DDDMMSS
            d, m, sec = s[:-4], s[-4:-2], s[-2:]
        return signe * (int(d) + int(m) / 60 + int(sec) / 3600)

    table, pays_tz = {}, {}
    for texte in textes:
        for ligne in texte.splitlines():
            if not ligne or ligne.startswith("#"):
                continue
            champs = ligne.split("\t")
            if len(champs) < 3:
                continue
            if "," not in champs[0]:  # zone.tab : un seul pays par ligne
                pays_tz[champs[2]] = champs[0]
            m = re.match(r"^([+-]\d+)([+-]\d+)$", champs[1])
            if m:
                try:
                    table[champs[2]] = (conv(m.group(1)), conv(m.group(2)))
                except ValueError:
                    pass

    noms = {}
    for ligne in iso.splitlines():
        if ligne and not ligne.startswith("#") and "\t" in ligne:
            code, nom = ligne.split("\t", 1)
            noms[code] = nom.strip()
    noms.update(PAYS_FR)
    return table, {tz: noms.get(cc, cc) for tz, cc in pays_tz.items()}


def charger_config():
    cfg = json.loads(json.dumps(CONFIG_DEFAUT))
    try:
        with open(CONFIG, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):  # ancien format : liste de villes
            data = {"villes": data}
        cfg.update(data)
    except Exception:
        pass
    return cfg


def sauver_config(cfg):
    try:
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showwarning("Sauvegarde", f"Impossible de sauvegarder :\n{e}")


def decoder_masque():
    raw = zlib.decompress(base64.b64decode(MASQUE_TERRE))
    octets_ligne = CARTE_L // 8
    lignes = []
    for r in range(CARTE_H):
        ligne = []
        for b in raw[r * octets_ligne:(r + 1) * octets_ligne]:
            for k in range(7, -1, -1):
                ligne.append(16 if (b >> k) & 1 else 0)  # 16 = palette terre
        lignes.append(ligne)
    return lignes


def palette_carte():
    """128 couleurs : (aurore 0-3) x 32 + (mer 0-15 | terre 16-31), nuit → jour."""
    def degrade(nuit, jour):
        out = []
        for i in range(16):
            f = i / 15
            bosse = 1 - abs(2 * f - 1)  # teinte chaude dans la grayline
            out.append((nuit[0] + (jour[0] - nuit[0]) * f + 45 * bosse,
                        nuit[1] + (jour[1] - nuit[1]) * f + 18 * bosse,
                        nuit[2] + (jour[2] - nuit[2]) * f - 5 * bosse))
        return out
    base = degrade((9, 17, 28), (36, 84, 126)) + degrade((26, 34, 28), (120, 138, 94))
    vert = (70, 235, 130)
    pal = []
    for f in (0, 0.25, 0.45, 0.65):
        for c in base:
            pal.append("#%02x%02x%02x" % tuple(
                int(max(0, min(255, c[i] + (vert[i] - c[i]) * f))) for i in range(3)))
    return pal


# ---------------------------------------------------------------- démarrage Windows
def raccourci_demarrage():
    dossier = os.path.join(os.environ.get("APPDATA", ""),
                           r"Microsoft\Windows\Start Menu\Programs\Startup")
    return os.path.join(dossier, "Horloge mondiale.lnk")


def demarrage_actif():
    return os.name == "nt" and os.path.exists(raccourci_demarrage())


def regler_demarrage(actif):
    import subprocess
    lnk = raccourci_demarrage()
    if not actif:
        if os.path.exists(lnk):
            os.remove(lnk)
        return
    if GELE:
        cible, args = sys.executable, ""
        dossier = os.path.dirname(sys.executable)
    else:
        cible = sys.executable
        pw = os.path.join(os.path.dirname(cible), "pythonw.exe")
        if os.path.exists(pw):
            cible = pw
        script = os.path.abspath(__file__)
        args, dossier = f'"{script}"', os.path.dirname(script)

    def q(s):
        return s.replace("'", "''")

    ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%s');"
          "$s.TargetPath='%s';$s.Arguments='%s';$s.WorkingDirectory='%s';$s.Save()"
          % (q(lnk), q(cible), q(args), q(dossier)))
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-Command", ps], check=True, capture_output=True,
                   creationflags=0x08000000)


# ================================================================ interface
POLICES = {"txt": "Segoe UI", "titre": "Segoe UI", "num": "Consolas", "mono": "Consolas"}


def choisir_polices(root):
    """Bahnschrift (Windows 10/11) pour un rendu « instrument », sinon repli."""
    fams = set(tkfont.families(root))

    def premier(*noms):
        for n in noms:
            if n in fams:
                return n
        return noms[-1]
    POLICES["txt"] = premier("Segoe UI Variable Text", "Segoe UI", "DejaVu Sans")
    POLICES["titre"] = premier("Bahnschrift", "Segoe UI Semibold", "Segoe UI", "DejaVu Sans")
    POLICES["num"] = premier("Bahnschrift", "Segoe UI", "DejaVu Sans")
    POLICES["mono"] = premier("Cascadia Mono", "Consolas", "DejaVu Sans Mono")


def F(role, taille, *style):
    return (POLICES[role], taille, *style)


def barre_titre_sombre(win):
    """Barre de titre sombre sous Windows 10/11."""
    if os.name != "nt":
        return
    try:
        import ctypes
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        val = ctypes.c_int(1)
        for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (selon la version)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ctypes.byref(val), ctypes.sizeof(val)) == 0:
                break
    except Exception:
        pass


def style_entree(e):
    e.configure(bg=PANNEAU2, fg=TEXTE, insertbackground=TEXTE, relief="flat",
                highlightthickness=1, highlightbackground=BORD, highlightcolor=UTC_COUL,
                font=F("txt", 10))
    return e


class Bouton(tk.Label):
    def __init__(self, parent, texte, cmd, primaire=False):
        self._bg = SEL if primaire else PANNEAU2
        self._sv = "#2f5576" if primaire else SURVOL
        super().__init__(parent, text=texte, bg=self._bg, fg=TEXTE, font=F("txt", 9),
                         padx=12, pady=4, cursor="hand2")
        self.cmd = cmd
        self.bind("<Enter>", lambda e: self.configure(bg=self._sv))
        self.bind("<Leave>", lambda e: self.configure(bg=self._bg))
        self.bind("<ButtonRelease-1>", lambda e: self.cmd())


class Bascule(tk.Frame):
    """Petit interrupteur à glissière + libellé."""
    def __init__(self, parent, texte, var, cmd=None, bg=FOND):
        super().__init__(parent, bg=bg, cursor="hand2")
        self.var, self.cmd = var, cmd
        self.cv = tk.Canvas(self, width=30, height=16, bg=bg, highlightthickness=0)
        self.cv.pack(side="left")
        self.lb = tk.Label(self, text=texte, bg=bg, font=F("txt", 9))
        self.lb.pack(side="left", padx=(6, 0))
        for w in (self, self.cv, self.lb):
            w.bind("<Button-1>", self.basculer)
        self.dessiner()

    def dessiner(self):
        on, c = self.var.get(), self.cv
        c.delete("all")
        fond = UTC_COUL if on else "#36414e"
        c.create_oval(1, 1, 15, 15, fill=fond, outline=fond)
        c.create_oval(15, 1, 29, 15, fill=fond, outline=fond)
        c.create_rectangle(8, 1, 22, 15, fill=fond, outline=fond)
        x = 22 if on else 8
        c.create_oval(x - 5, 3, x + 5, 13, fill="#ffffff" if on else "#aab4bf", outline="")
        self.lb.configure(fg=TEXTE if on else TEXTE_DIM)

    def basculer(self, e=None):
        self.var.set(not self.var.get())
        self.dessiner()
        if self.cmd:
            self.cmd()


class Segments(tk.Frame):
    """Sélecteur segmenté (Pays | Carte | Compact)."""
    def __init__(self, parent, options, cmd):
        super().__init__(parent, bg=BORD, padx=1, pady=1)
        self.items, self.actif = {}, None
        for i, (cle, texte) in enumerate(options):
            l = tk.Label(self, text=texte, font=F("txt", 9), bg=PANNEAU, fg=TEXTE_DIM,
                         padx=16, pady=4, cursor="hand2")
            l.pack(side="left", padx=(0 if i == 0 else 1, 0))
            l.bind("<ButtonRelease-1>", lambda e, c=cle: cmd(c))
            l.bind("<Enter>", lambda e, c=cle: c != self.actif and self.items[c].configure(bg=SURVOL))
            l.bind("<Leave>", lambda e, c=cle: c != self.actif and self.items[c].configure(bg=PANNEAU))
            self.items[cle] = l

    def choisir(self, cle):
        self.actif = cle
        for c, l in self.items.items():
            l.configure(bg=SEL if c == cle else PANNEAU, fg=TEXTE if c == cle else TEXTE_DIM)


class Afficheur(tk.Canvas):
    """Heure HH:MM (+ :SS plus petit) avec chiffres sur grille fixe : rien ne bouge."""
    def __init__(self, parent, couleur, taille, secondes=True, couleur_sec=None,
                 bg=PANNEAU, ratio_sec=0.5):
        g = tkfont.Font(family=POLICES["num"], size=taille, weight="bold")
        pt = tkfont.Font(family=POLICES["num"], size=max(8, int(taille * ratio_sec)), weight="bold")
        self._polices = (g, pt)
        wd = max(g.measure(str(d)) for d in range(10))
        wdp = max(pt.measure(str(d)) for d in range(10))
        asc, ascp = g.metrics("ascent"), pt.metrics("ascent")
        haut = asc + g.metrics("descent") // 2
        super().__init__(parent, bg=bg, highlightthickness=0, height=haut)
        disp = [("d", g, wd), ("d", g, wd), (":", g, g.measure(":") + 2),
                ("d", g, wd), ("d", g, wd)]
        if secondes:
            disp += [(":", pt, pt.measure(":") + 4), ("d", pt, wdp), ("d", pt, wdp)]
        x, self.cells = 0, []
        for k, f, w in disp:
            petit = f is pt
            it = self.create_text(x + w / 2, asc - ascp if petit else 0, anchor="n", font=f,
                                  text=":" if k == ":" else "0",
                                  fill=(couleur_sec or couleur) if petit else couleur)
            if k == "d":
                self.cells.append(it)
            x += w
        self.configure(width=x)

    def regler(self, h, m, s=None):
        txt = f"{h:02d}{m:02d}" + (f"{s:02d}" if s is not None else "")
        for it, ch in zip(self.cells, txt):
            self.itemconfigure(it, text=ch)


COULEURS_ETAT = {"jour": ACCENT, "grayline": CORAIL, "crépuscule": LUNE, "nuit": LUNE}
ICONES_ETAT = {"jour": "☀", "grayline": "◐", "crépuscule": "☾", "nuit": "☾"}


def couleur_barre(h):
    if h > 0:
        return "#b88a2e"
    if h > -6:
        return "#a0522d"
    if h > -12:
        return "#3b3560"
    return "#1b2133"


class CarteVille(tk.Frame):
    def __init__(self, parent, app, ville, secondes):
        super().__init__(parent, bg=PANNEAU, highlightthickness=1, highlightbackground=BORD)
        self.app = app
        self.ville = ville
        self.tz = ZoneInfo(ville["tz"])
        self.secondes = secondes

        self.bande = tk.Frame(self, bg=ACCENT, width=3)
        self.bande.pack(side="left", fill="y")
        f = tk.Frame(self, bg=PANNEAU, padx=12, pady=8)
        f.pack(side="left", fill="both", expand=True)

        haut = tk.Frame(f, bg=PANNEAU)
        haut.pack(fill="x")
        self.l_nom = tk.Label(haut, text=ville["nom"], font=F("titre", 12, "bold"),
                              fg=TEXTE, bg=PANNEAU, anchor="w")
        self.l_nom.pack(side="left")
        self.l_icone = tk.Label(haut, text="", font=F("txt", 12), fg=ACCENT, bg=PANNEAU)
        self.l_icone.pack(side="right")

        self.aff = Afficheur(f, TEXTE, 26, secondes=secondes, couleur_sec=TEXTE_DIM)
        self.aff.pack(anchor="w", pady=(2, 0))
        self.l_info = tk.Label(f, text="", font=F("txt", 9), fg=TEXTE_DIM, bg=PANNEAU, anchor="w")
        self.l_info.pack(fill="x")
        self.barre = tk.Canvas(f, width=1, height=5, bg=PANNEAU, highlightthickness=0)
        self.barre.pack(fill="x", pady=(6, 0))
        self.barre.bind("<Configure>", lambda e: self.dessiner_barre(force=True))
        self._minute_barre = None
        self._dernier = None

        self.widgets = [self, self.bande, f, haut, self.l_nom, self.l_icone,
                        self.aff, self.l_info, self.barre]
        for w in self.widgets:
            w.bind("<Button-3>", self.menu)
            w.bind("<Enter>", lambda e: self.configure(highlightbackground="#3c4b5c"))
            w.bind("<Leave>", lambda e: self.configure(highlightbackground=BORD))

    def menu(self, event):
        m = tk.Menu(self, tearoff=0)
        m.add_command(label=f"Supprimer {self.ville['nom']}",
                      command=lambda: self.app.supprimer(self.ville))
        m.tk_popup(event.x_root, event.y_root)

    def dessiner_barre(self, force=False):
        """Barre 0 h → 24 h (heure du pays) : jour / grayline / nuit + position actuelle."""
        if not self._dernier or self.ville.get("lat") is None:
            return
        dt = self._dernier
        cle = (dt.hour, dt.minute)
        if not force and cle == self._minute_barre:
            return
        self._minute_barre = cle
        c = self.barre
        w = max(c.winfo_width(), 10)
        c.delete("all")
        minuit = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        n = 96
        for i in range(n):
            t = (minuit + timedelta(minutes=15 * i + 7)).astimezone(timezone.utc)
            h = hauteur_soleil(self.ville["lat"], self.ville["lon"], soleil(t))
            x0, x1 = w * i / n, w * (i + 1) / n
            c.create_rectangle(x0, 0, x1 + 1, 5, fill=couleur_barre(h), outline="")
        x = w * (dt.hour * 60 + dt.minute) / 1440
        c.create_rectangle(x - 1, 0, x + 1, 5, fill="#ffffff", outline="")

    def maj(self, now_utc, sol):
        dt = now_utc.astimezone(self.tz)
        self._dernier = dt
        if self.ville.get("lat") is not None:
            etat = etat_soleil(hauteur_soleil(self.ville["lat"], self.ville["lon"], sol))
        else:
            etat = "jour" if 7 <= dt.hour < 19 else "nuit"
        coul = COULEURS_ETAT[etat]
        self.bande.configure(bg=coul)
        self.l_icone.configure(text=ICONES_ETAT[etat], fg=coul)
        self.aff.regler(dt.hour, dt.minute, dt.second if self.secondes else None)
        self.l_info.configure(text=f"{fmt_date(dt)}  ·  {fmt_offset(dt)}")
        self.dessiner_barre()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        choisir_polices(self)
        self.title(APP)
        self.configure(bg=FOND)
        self.minsize(780, 420)
        self.option_add("*Font", F("txt", 9))
        try:
            self._icone = tk.PhotoImage(data=ICONE_PNG)
            self.iconphoto(True, self._icone)
        except Exception:
            pass

        self.cfg = charger_config()
        self.coords_tz, self.pays_tz = coords_fuseaux()
        self.secondes = tk.BooleanVar(value=self.cfg.get("secondes", False))
        self.premier_plan = tk.BooleanVar(value=self.cfg.get("premier_plan", False))
        self.attributes("-topmost", self.premier_plan.get())
        self.maj_qth()

        self.villes = []
        for v in self.cfg["villes"]:
            try:
                ZoneInfo(v["tz"])
            except (ZoneInfoNotFoundError, KeyError, ValueError):
                continue
            if v.get("nom") in ANCIENS_NOMS and \
                    any(d["tz"] == v["tz"] for d in VILLES_DEFAUT):
                v["nom"] = ANCIENS_NOMS[v["nom"]]
            if v.get("lat") is None and v["tz"] in self.coords_tz:
                v["lat"], v["lon"] = self.coords_tz[v["tz"]]
            self.villes.append(v)

        self.construire_entete()
        self.construire_barre()
        self.page_villes = tk.Frame(self, bg=FOND)
        self.page_carte = tk.Frame(self, bg=FOND)
        self.construire_page_villes()
        self.construire_page_carte()

        self.compact = None
        self.vue = None
        self._derniere_seconde = None
        self._derniere_minute_carte = None
        vue = self.cfg.get("vue", "villes")
        self.afficher_vue("carte" if vue == "carte" else "villes")
        if vue == "compact":
            self.after(50, self.ouvrir_compact)
        self.protocol("WM_DELETE_WINDOW", self.quitter)
        barre_titre_sombre(self)
        self.tick()

    # ------------------------------------------------------------ config
    def sauver(self):
        self.cfg["villes"] = self.villes
        self.cfg["secondes"] = self.secondes.get()
        self.cfg["premier_plan"] = self.premier_plan.get()
        sauver_config(self.cfg)

    def maj_qth(self):
        try:
            self.qth = locator_vers_latlon(self.cfg.get("locator", ""))
        except ValueError:
            self.qth = None

    def quitter(self):
        self.sauver()
        self.destroy()

    # ------------------------------------------------------------ en-tête
    def panneau(self, parent, accent):
        cadre = tk.Frame(parent, bg=PANNEAU, highlightthickness=1, highlightbackground=BORD)
        tk.Frame(cadre, bg=accent, height=2).pack(fill="x")
        inner = tk.Frame(cadre, bg=PANNEAU, padx=16, pady=10)
        inner.pack(fill="both", expand=True)
        return cadre, inner

    def construire_entete(self):
        tete = tk.Frame(self, bg=FOND, padx=16)
        tete.pack(fill="x", pady=(14, 10))

        def bloc(col, titre, coul, sous_titre):
            cadre, f = self.panneau(tete, coul)
            cadre.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 10, 0))
            ligne = tk.Frame(f, bg=PANNEAU)
            ligne.pack(fill="x")
            tk.Label(ligne, text=titre, font=F("titre", 11, "bold"), fg=coul,
                     bg=PANNEAU).pack(side="left")
            tk.Label(ligne, text=sous_titre, font=F("txt", 8), fg=TEXTE_DIM,
                     bg=PANNEAU).pack(side="left", padx=(8, 0), pady=(2, 0))
            aff = Afficheur(f, coul, 38, secondes=True)
            aff.pack(anchor="w", pady=(4, 2))
            d = tk.Label(f, text="", font=F("txt", 9), fg=TEXTE_DIM, bg=PANNEAU)
            d.pack(anchor="w")
            return aff, d

        self.aff_utc, self.l_utc_date = bloc(0, "UTC", UTC_COUL, "temps universel")
        self.aff_loc, self.l_loc_date = bloc(1, "LOCAL", ACCENT, "heure du PC")

        cadre, f = self.panneau(tete, QTH_COUL)
        cadre.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        tete.columnconfigure(2, weight=1)
        ligne = tk.Frame(f, bg=PANNEAU)
        ligne.pack(fill="x")
        self.l_qth_titre = tk.Label(ligne, text="", font=F("titre", 13, "bold"),
                                    fg=QTH_COUL, bg=PANNEAU)
        self.l_qth_titre.pack(side="left")
        self.l_qth_loc = tk.Label(ligne, text="", font=F("mono", 10), fg=TEXTE_DIM, bg=PANNEAU)
        self.l_qth_loc.pack(side="left", padx=(8, 0), pady=(3, 0))
        etat = tk.Frame(f, bg=PANNEAU)
        etat.pack(fill="x", pady=(10, 0))
        self.l_qth_icone = tk.Label(etat, text="", font=F("txt", 20), fg=ACCENT, bg=PANNEAU)
        self.l_qth_icone.pack(side="left")
        col = tk.Frame(etat, bg=PANNEAU)
        col.pack(side="left", padx=(10, 0))
        self.l_qth_soleil = tk.Label(col, text="", font=F("titre", 12, "bold"), fg=TEXTE,
                                     bg=PANNEAU, anchor="w")
        self.l_qth_soleil.pack(anchor="w")
        self.l_qth_hauteur = tk.Label(col, text="", font=F("txt", 9), fg=TEXTE_DIM,
                                      bg=PANNEAU, anchor="w")
        self.l_qth_hauteur.pack(anchor="w")
        self.l_qth_lever = tk.Label(f, text="", font=F("txt", 10), fg=TEXTE, bg=PANNEAU,
                                    anchor="w")
        self.l_qth_lever.pack(anchor="w", pady=(8, 0))
        self._jour_lever = None

    def bouton(self, parent, texte, cmd, primaire=False):
        return Bouton(parent, texte, cmd, primaire)

    def construire_barre(self):
        barre = tk.Frame(self, bg=FOND, padx=16)
        barre.pack(fill="x", pady=(0, 4))
        Bascule(barre, "Secondes", self.secondes, self.basculer_secondes).pack(side="left")
        Bascule(barre, "Toujours au premier plan", self.premier_plan,
                self.basculer_premier_plan).pack(side="left", padx=(18, 0))
        self.bouton(barre, "⚙  Réglages", self.dialogue_reglages).pack(side="right")
        self.segments = Segments(barre, (("villes", "Pays"), ("carte", "Carte"),
                                         ("compact", "Compact")), self.afficher_vue)
        self.segments.pack(side="right", padx=(0, 10))

    def basculer_secondes(self):
        self.sauver()
        self.construire_grille()

    def basculer_premier_plan(self):
        self.attributes("-topmost", self.premier_plan.get())
        self.sauver()

    def afficher_vue(self, vue):
        if vue == "compact":
            self.ouvrir_compact()
            return
        self.page_villes.pack_forget()
        self.page_carte.pack_forget()
        (self.page_carte if vue == "carte" else self.page_villes).pack(
            fill="both", expand=True)
        self.segments.choisir(vue)
        self.vue = vue
        self.cfg["vue"] = vue
        self.sauver()
        if vue == "carte":
            self.dessiner_carte()

    # ------------------------------------------------------------ page pays
    def construire_page_villes(self):
        outils = tk.Frame(self.page_villes, bg=FOND, padx=16)
        outils.pack(fill="x", pady=(6, 0))
        leg = tk.Frame(outils, bg=FOND)
        leg.pack(side="left")
        for coul, txt in ((ACCENT, "jour"), (CORAIL, "grayline"), (LUNE, "nuit")):
            tk.Frame(leg, bg=coul, width=10, height=10).pack(side="left", padx=(0, 4))
            tk.Label(leg, text=txt, font=F("txt", 8), fg=TEXTE_DIM, bg=FOND).pack(
                side="left", padx=(0, 12))
        tk.Label(leg, text="·   clic droit sur un pays pour le supprimer", font=F("txt", 8),
                 fg=TEXTE_DIM, bg=FOND).pack(side="left")
        self.bouton(outils, "+  Ajouter", self.dialogue_ajout, primaire=True).pack(side="right")
        self.bouton(outils, "Défaut", self.reinitialiser).pack(side="right", padx=6)

        self.grille = tk.Frame(self.page_villes, bg=FOND, padx=11, pady=6)
        self.grille.pack(fill="both", expand=True, pady=(0, 8))
        self.cartes = []
        self.construire_grille()

    def construire_grille(self):
        for c in self.cartes:
            c.destroy()
        self.cartes = []
        sec = self.secondes.get()
        for i, v in enumerate(self.villes):
            c = CarteVille(self.grille, self, v, sec)
            c.grid(row=i // COLONNES, column=i % COLONNES, padx=5, pady=5, sticky="nsew")
            self.cartes.append(c)
        for col in range(COLONNES):
            self.grille.columnconfigure(col, weight=1, uniform="col")
        self._derniere_seconde = None
        self._derniere_minute_carte = None

    def supprimer(self, ville):
        self.villes = [v for v in self.villes if v is not ville]
        self.sauver()
        self.construire_grille()

    def reinitialiser(self):
        if messagebox.askyesno("Réinitialiser", "Revenir à la liste de villes par défaut ?"):
            self.villes = json.loads(json.dumps(VILLES_DEFAUT))
            self.sauver()
            self.construire_grille()

    def entrees_pays(self):
        """Liste (libellé, fuseau, nom proposé) triée par pays."""
        import unicodedata
        dispo = available_timezones()
        par_pays = {}
        for tz, pays in self.pays_tz.items():
            if tz in dispo:
                par_pays.setdefault(pays, []).append(tz)
        entrees = []
        for pays, fuseaux in par_pays.items():
            for tz in fuseaux:
                ville = tz.split("/")[-1].replace("_", " ")
                nom = pays if len(fuseaux) == 1 else f"{pays} ({ville})"
                entrees.append((f"{pays}  —  {ville}", tz, nom))

        def cle(e):
            return unicodedata.normalize("NFD", e[0]).encode("ascii", "ignore").decode().lower()
        entrees.sort(key=cle)
        return entrees

    def dialogue_ajout(self):
        import unicodedata
        entrees = self.entrees_pays()
        if not entrees:
            messagebox.showerror("Fuseaux", "Aucun fuseau horaire disponible.\n"
                                 "Installe-les avec :  py -m pip install tzdata")
            return

        def sans_accent(t):
            return unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode().lower()

        index = [sans_accent(lib + " " + tz) for lib, tz, _ in entrees]

        d = tk.Toplevel(self)
        d.title("Ajouter un pays")
        d.configure(bg=FOND, padx=16, pady=14)
        d.transient(self)
        barre_titre_sombre(d)
        d.grab_set()

        tk.Label(d, text="Recherche (pays ou ville, ex. Canada, Italie, Tokyo)",
                 bg=FOND, fg=TEXTE_DIM, font=F("txt", 9)).grid(row=0, column=0, sticky="w")
        e_rech = style_entree(tk.Entry(d, width=40))
        e_rech.grid(row=1, column=0, sticky="we", ipady=3, pady=(2, 0))
        lb = tk.Listbox(d, height=14, width=46, bg=PANNEAU, fg=TEXTE, relief="flat",
                        highlightthickness=1, highlightbackground=BORD,
                        highlightcolor=BORD, selectbackground=SEL, selectforeground=TEXTE,
                        activestyle="none", font=F("txt", 10))
        lb.grid(row=2, column=0, sticky="nsew", pady=8)
        tk.Label(d, text="Nom affiché", bg=FOND, fg=TEXTE_DIM,
                 font=F("txt", 9)).grid(row=3, column=0, sticky="w")
        e_nom = style_entree(tk.Entry(d, width=40))
        e_nom.grid(row=4, column=0, sticky="we", ipady=3, pady=(2, 10))
        visibles = []

        def filtrer(*_):
            q = sans_accent(e_rech.get().strip())
            lb.delete(0, "end")
            visibles.clear()
            for e, txt in zip(entrees, index):
                if q in txt:
                    visibles.append(e)
                    lb.insert("end", e[0])

        def choisir(_=None):
            sel = lb.curselection()
            if sel:
                e_nom.delete(0, "end")
                e_nom.insert(0, visibles[sel[0]][2])

        def valider(_=None):
            sel = lb.curselection()
            if not sel:
                messagebox.showinfo("Ajouter", "Choisis un pays dans la liste.", parent=d)
                return
            _, tz, nom = visibles[sel[0]]
            v = {"nom": e_nom.get().strip() or nom, "tz": tz}
            if tz in self.coords_tz:
                v["lat"], v["lon"] = self.coords_tz[tz]
            self.villes.append(v)
            self.sauver()
            self.construire_grille()
            d.destroy()

        e_rech.bind("<KeyRelease>", filtrer)
        lb.bind("<<ListboxSelect>>", choisir)
        lb.bind("<Double-Button-1>", valider)
        d.bind("<Return>", valider)
        self.bouton(d, "Ajouter", valider, primaire=True).grid(row=5, column=0, sticky="e")
        filtrer()
        e_rech.focus_set()

    # ------------------------------------------------------------ page carte
    def construire_page_carte(self):
        p = self.page_carte
        cadre = tk.Frame(p, bg=BORD, padx=1, pady=1)
        cadre.pack(pady=(6, 0))
        self.canvas = tk.Canvas(cadre, width=CARTE_L, height=CARTE_H, bg="#09111c",
                                highlightthickness=0)
        self.canvas.pack()
        self.l_survol = tk.Label(p, text="Survole la carte : locator, distance et azimut depuis le QTH",
                                 font=F("mono", 9), fg=TEXTE_DIM, bg=FOND)
        self.l_survol.pack(pady=(4, 0))

        # --- calques + légende MUF
        cal = tk.Frame(p, bg=FOND)
        cal.pack(fill="x", padx=20, pady=(6, 0))
        calques = self.cfg.setdefault("calques", {"muf": True, "stations": True, "aurore": True})
        self.v_calques = {}
        for cle, texte in (("muf", "MUF"), ("stations", "Ionosondes"), ("aurore", "Ovale auroral")):
            v = tk.BooleanVar(value=calques.get(cle, True))
            self.v_calques[cle] = v
            Bascule(cal, texte, v, self.changer_calques).pack(side="left", padx=(0, 16))
        leg = tk.Frame(cal, bg=FOND)
        leg.pack(side="right")
        tk.Label(leg, text="MUF", font=F("txt", 8), fg=TEXTE_DIM, bg=FOND).pack(side="left", padx=(0, 4))
        bornes = [5] + [lim for lim, _ in ECHELLE_MUF[:-1]]
        for lim, (_, c) in zip(bornes, ECHELLE_MUF):
            tk.Label(leg, text=f"{lim}", font=F("titre", 8, "bold"), fg="#0b0f14", bg=c,
                     width=3).pack(side="left")
        tk.Label(leg, text="MHz", font=F("txt", 8), fg=TEXTE_DIM, bg=FOND).pack(side="left", padx=(4, 0))

        # --- tableau des indices
        tab = tk.Frame(p, bg=FOND)
        tab.pack(fill="x", padx=20, pady=(10, 0))
        cadre_g, gauche = self.panneau(tab, UTC_COUL)
        cadre_g.pack(side="left", fill="both", expand=True)
        gauche.configure(padx=10, pady=6)
        tk.Label(gauche, text="INDICES SOLAIRES", font=F("titre", 8, "bold"), fg=TEXTE_DIM,
                 bg=PANNEAU).grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 2))
        self.ind = {}
        cases = [("solarflux", "SFI"), ("sunspots", "SSN"), ("aindex", "A"), ("kindex", "K"),
                 ("xray", "Rayons X"), ("solarwind", "Vent km/s"), ("magneticfield", "Bz nT"),
                 ("geomagfield", "Géomag."), ("signalnoise", "Bruit"), ("aurora", "Aurore")]
        for i, (cle, titre) in enumerate(cases):
            f = tk.Frame(gauche, bg=PANNEAU)
            f.grid(row=1 + i // 5, column=i % 5, padx=(0, 14), pady=2, sticky="w")
            tk.Label(f, text=titre, font=F("txt", 8), fg=TEXTE_DIM, bg=PANNEAU).pack(anchor="w")
            l = tk.Label(f, text="—", font=F("num", 14, "bold"), fg=TEXTE, bg=PANNEAU,
                         width=8 if cle == "geomagfield" else 6, anchor="w")
            l.pack(anchor="w")
            self.ind[cle] = l

        cadre_d, droite = self.panneau(tab, ACCENT)
        cadre_d.pack(side="right", fill="y", padx=(10, 0))
        droite.configure(padx=10, pady=6)
        tk.Label(droite, text="BANDES HF", font=F("titre", 8, "bold"), fg=TEXTE_DIM,
                 bg=PANNEAU).grid(row=0, column=0, sticky="w")
        for j, t in enumerate(("Jour", "Nuit")):
            tk.Label(droite, text=t, font=F("txt", 8), fg=TEXTE_DIM,
                     bg=PANNEAU).grid(row=0, column=j + 1)
        self.cases_bandes = {}
        for i, bande in enumerate(("80m-40m", "30m-20m", "17m-15m", "12m-10m")):
            tk.Label(droite, text=bande.replace("m-", "-"), font=F("num", 10, "bold"),
                     fg=TEXTE, bg=PANNEAU).grid(row=i + 1, column=0, sticky="w", padx=(0, 8))
            for j, moment in enumerate(("day", "night")):
                l = tk.Label(droite, text="—", font=F("titre", 9, "bold"), fg="#ffffff",
                             bg=PANNEAU2, width=9)
                l.grid(row=i + 1, column=j + 1, padx=2, pady=1)
                self.cases_bandes[(bande, moment)] = l

        self.l_muf_qth = tk.Label(p, text="", font=F("txt", 9), fg=TEXTE, bg=FOND, anchor="w")
        self.l_muf_qth.pack(fill="x", padx=20, pady=(8, 0))
        self.l_vhf = tk.Label(p, text="", font=F("txt", 9), fg=TEXTE_DIM, bg=FOND, anchor="w")
        self.l_vhf.pack(fill="x", padx=20)
        self.l_sources = tk.Label(p, text="Chargement des données de propagation…",
                                  font=F("txt", 8), fg=TEXTE_DIM, bg=FOND, anchor="w")
        self.l_sources.pack(fill="x", padx=20, pady=(2, 10))

        # --- image de la carte
        self.masque = decoder_masque()
        self.base = self.masque
        self.palette = palette_carte()
        self.img = [tk.PhotoImage(width=CARTE_L, height=CARTE_H) for _ in range(2)]
        self.img_actif = 0
        self.item_img = self.canvas.create_image(0, 0, anchor="nw", image=self.img[0])
        for lon in range(-150, 180, 30):
            x = (lon + 180) * 2
            self.canvas.create_line(x, 0, x, CARTE_H, fill="#33465a", dash=(2, 4))
        for lat in range(-60, 90, 30):
            y = (90 - lat) * 2
            self.canvas.create_line(0, y, CARTE_L, y,
                                    fill="#4a5f75" if lat == 0 else "#33465a", dash=(2, 4))
        self._rendu = None
        self.sol_carte = None
        self.canvas.bind("<Motion>", self.survol)
        self.canvas.bind("<Leave>", lambda e: self.l_survol.configure(text=""))

        # --- données de propagation
        self.prop = {}
        self._prop_nouvelles = None
        self._prop_en_cours = False
        self._prop_derniere = 0.0

    def changer_calques(self):
        self.cfg["calques"] = {k: v.get() for k, v in self.v_calques.items()}
        self.sauver()
        self.appliquer_aurore()
        self.dessiner_carte()

    # ---- téléchargement en arrière-plan
    def lancer_maj_donnees(self):
        if self._prop_en_cours:
            return
        self._prop_en_cours = True
        self._prop_derniere = time.time()

        def travail():
            self._prop_nouvelles = recuperer_donnees()
            self._prop_en_cours = False
        threading.Thread(target=travail, daemon=True).start()

    def integrer_donnees(self, res):
        for cle in ("solaire", "stations", "contours", "aurore"):
            if cle in res:
                self.prop[cle] = res[cle]
                self.prop["heure_" + cle] = res["heure"]
        self.prop["erreurs"] = res["erreurs"]
        self.appliquer_aurore()
        self.maj_tableau()
        if self.vue == "carte":
            self.dessiner_carte()

    def appliquer_aurore(self):
        grille = self.prop.get("aurore")
        if not grille or not self.v_calques["aurore"].get():
            self.base = self.masque
            return
        base = []
        for r in range(CARTE_H):
            gl = grille[min(180, max(0, int(round(90 - (r + 0.5) * 0.5)) + 90))]
            ligne = []
            for c, t in enumerate(self.masque[r]):
                v = gl[int(-180 + (c + 0.5) * 0.5) % 360]
                ligne.append(t + (0 if v < 4 else 32 if v < 20 else 64 if v < 50 else 96))
            base.append(ligne)
        self.base = base

    def maj_tableau(self):
        sol = self.prop.get("solaire")
        if sol:
            for cle, l in self.ind.items():
                val = sol.get(cle, "") or "—"
                if cle == "geomagfield":
                    val = FR_GEOMAG.get(val.upper(), val.lower())
                elif cle == "solarwind":
                    try:
                        val = f"{float(val):.0f}"
                    except ValueError:
                        pass
                l.configure(text=val, fg=couleur_indice(cle, sol.get(cle, "")))
            for (bande, moment), l in self.cases_bandes.items():
                txt, coul = FR_BANDES.get(sol["bandes"].get((bande, moment), ""), ("—", PANNEAU2))
                l.configure(text=txt, bg=coul)
            vhf = []
            for nom, lieu, val in sol.get("vhf", []):
                etiquette = VHF_NOMS.get((nom, lieu), f"{nom} {lieu}")
                vhf.append(f"{etiquette} : {'fermé' if 'closed' in val.lower() else val}")
            self.l_vhf.configure(text="VHF  ·  " + "   ".join(vhf) if vhf else "")
        # MUF de l'ionosonde la plus proche du QTH
        stations = self.prop.get("stations") or []
        if self.qth and stations:
            d, i = min((distance_azimut(self.qth[0], self.qth[1], s["lat"], s["lon"])[0], i)
                       for i, s in enumerate(stations))
            st = stations[i]
            fof2 = f"  ·  foF2 {st['fof2']:.1f} MHz" if st.get("fof2") else ""
            self.l_muf_qth.configure(
                text=f"Ionosonde la plus proche : {st['nom']} ({fmt_km(d)})  ·  "
                     f"MUF(3000) {st['muf']:.1f} MHz{fof2}  ·  il y a {st['age']:.0f} min")
        elif self.qth:
            self.l_muf_qth.configure(text="Ionosonde la plus proche : pas de mesure récente")
        # sources
        morceaux = []
        if sol:
            morceaux.append(f"Indices N0NBH : {sol.get('updated', '')}")
        for cle, nom in (("stations", "KC2G"), ("aurore", "NOAA")):
            h = self.prop.get("heure_" + cle)
            if h:
                morceaux.append(f"{nom} : {h:%H:%M} UTC")
        noms_err = {"solaire": "N0NBH", "stations": "KC2G", "contours": "KC2G (MUF)",
                    "aurore": "NOAA"}
        err = [noms_err[e] for e in self.prop.get("erreurs", [])]
        if err:
            morceaux.append("indisponible : " + ", ".join(err))
        self.l_sources.configure(text="  ·  ".join(morceaux) + "  ·  mise à jour toutes les 15 min",
                                 fg=ORANGE if err else TEXTE_DIM)

    @staticmethod
    def xy(lat, lon):
        return (lon + 180) * 2, (90 - lat) * 2

    def dessiner_carte(self):
        """Lance un rendu jour/nuit progressif (évite de figer la fenêtre)."""
        now = datetime.now(timezone.utc)
        self.sol_carte = soleil(now)
        self._derniere_minute_carte = (now.hour, now.minute)
        self._rendu = self._generateur_rendu(self.sol_carte)
        self._etape_rendu(self._rendu)

    def _etape_rendu(self, gen):
        if gen is not self._rendu:
            return  # un rendu plus récent a été lancé
        try:
            next(gen)
            self.after(1, self._etape_rendu, gen)
        except StopIteration:
            pass

    def _generateur_rendu(self, sol):
        decl, sublon = sol
        sd, cd = math.sin(decl), math.cos(decl)
        cos_h = [math.cos(math.radians(-180 + (c + 0.5) * 0.5 - sublon))
                 for c in range(CARTE_L)]
        s0, s1 = math.sin(math.radians(-12)), math.sin(math.radians(2))
        k = 15.999 / (s1 - s0)
        P = self.palette
        dest = self.img[1 - self.img_actif]
        pas = 40
        for r0 in range(0, CARTE_H, pas):
            lignes = []
            for r in range(r0, min(r0 + pas, CARTE_H)):
                lat = math.radians(90 - (r + 0.5) * 0.5)
                a = math.sin(lat) * sd - s0
                b = math.cos(lat) * cd
                lignes.append("{" + " ".join(
                    [P[t + (15 if (v := int((a + b * ch) * k)) > 15 else (v if v > 0 else 0))]
                     for t, ch in zip(self.base[r], cos_h)]) + "}")
            dest.put(" ".join(lignes), to=(0, r0))
            yield
        self.img_actif = 1 - self.img_actif
        self.canvas.itemconfigure(self.item_img, image=dest)
        self.dessiner_surcouches(sol)

    def dessiner_surcouches(self, sol):
        cv = self.canvas
        cv.delete("ov")
        decl, sublon = sol
        # contours de MUF
        if self.v_calques["muf"].get():
            for niveau, pts_geo in self.prop.get("contours") or []:
                coul = couleur_muf(niveau)
                segment = []
                prec = None
                for lon, lat in pts_geo:
                    if prec is not None and abs(lon - prec) > 180:  # passage de l'antiméridien
                        if len(segment) >= 4:
                            cv.create_line(*segment, fill=coul, width=2, tags="ov")
                        segment = []
                    segment += self.xy(lat, lon)
                    prec = lon
                if len(segment) >= 4:
                    cv.create_line(*segment, fill=coul, width=2, tags="ov")
                if len(pts_geo) > 30:
                    lon, lat = pts_geo[len(pts_geo) // 2]
                    x, y = self.xy(lat, lon)
                    cv.create_text(x, y, text=f"{niveau:g}", fill=coul,
                                   font=("Segoe UI", 8, "bold"), tags="ov")
        # ionosondes
        if self.v_calques["stations"].get():
            for st in self.prop.get("stations") or []:
                x, y = self.xy(st["lat"], st["lon"])
                cv.create_rectangle(x - 3, y - 3, x + 3, y + 3, fill=couleur_muf(st["muf"]),
                                    outline="#000000", tags="ov")
        # terminateur
        sd = math.sin(decl) if abs(decl) > 1e-4 else 1e-4
        pts = []
        for i in range(0, 361, 2):
            lon = -180 + i
            lat = math.degrees(math.atan(-math.cos(math.radians(lon - sublon)) *
                                         math.cos(decl) / sd))
            pts += self.xy(lat, lon)
        cv.create_line(*pts, fill=ACCENT, width=2, smooth=True, tags="ov")
        # villes
        for v in self.villes:
            if v.get("lat") is not None:
                x, y = self.xy(v["lat"], v["lon"])
                cv.create_oval(x - 3, y - 3, x + 3, y + 3, fill=TEXTE,
                               outline="#000000", tags="ov")
        # soleil
        x, y = self.xy(math.degrees(decl), sublon)
        cv.create_oval(x - 9, y - 9, x + 9, y + 9, fill="#ffd54a", outline="#fff3b0",
                       width=2, tags="ov")
        # QTH
        if self.qth:
            x, y = self.xy(*self.qth)
            cv.create_oval(x - 5, y - 5, x + 5, y + 5, fill=QTH_COUL, outline="#ffffff",
                           width=1, tags="ov")
            cv.create_text(x + 8, y - 8, text=self.cfg.get("indicatif", "QTH"),
                           anchor="sw", fill="#ffffff", font=("Segoe UI", 9, "bold"),
                           tags="ov")

    def survol(self, e):
        lon = e.x / 2 - 180
        lat = 90 - e.y / 2
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return
        now = datetime.now(timezone.utc)
        h = hauteur_soleil(lat, lon, soleil(now))
        txt = f"{latlon_vers_locator(lat, lon)}  {fmt_latlon(lat, lon)}"
        # ionosonde proche ?
        if self.v_calques["stations"].get():
            for st in self.prop.get("stations") or []:
                x, y = self.xy(st["lat"], st["lon"])
                if abs(x - e.x) <= 5 and abs(y - e.y) <= 5:
                    fof2 = f"  foF2 {st['fof2']:.1f}" if st.get("fof2") else ""
                    self.l_survol.configure(
                        text=f"{st['nom']}  ·  MUF(3000) {st['muf']:.1f} MHz{fof2}"
                             f"  ·  il y a {st['age']:.0f} min")
                    return
        # ville proche ?
        for v in self.villes:
            if v.get("lat") is None:
                continue
            x, y = self.xy(v["lat"], v["lon"])
            if abs(x - e.x) <= 6 and abs(y - e.y) <= 6:
                dt = now.astimezone(ZoneInfo(v["tz"]))
                lat, lon = v["lat"], v["lon"]
                h = hauteur_soleil(lat, lon, soleil(now))
                txt = f"{v['nom']} {dt:%H:%M} ({fmt_date(dt)})  {latlon_vers_locator(lat, lon)}"
                break
        if self.qth:
            d, az = distance_azimut(self.qth[0], self.qth[1], lat, lon)
            txt += f"  ·  {fmt_km(d)}  az {az:03.0f}°"
        txt += f"  ·  soleil {h:+.0f}° {etat_soleil(h)}"
        self.l_survol.configure(text=txt)

    # ------------------------------------------------------------ compact
    def ouvrir_compact(self):
        if self.compact:
            return
        self.vue_avant_compact = self.vue or "villes"
        self.cfg["vue"] = "compact"
        self.sauver()
        self.withdraw()

        c = tk.Toplevel(self)
        c.overrideredirect(True)
        c.attributes("-topmost", True)
        c.configure(bg=BORD, padx=1, pady=1)
        corps = tk.Frame(c, bg=PANNEAU)
        corps.pack()
        bande = tk.Frame(corps, bg=UTC_COUL, width=3)
        bande.pack(side="left", fill="y")
        f = tk.Frame(corps, bg=PANNEAU, padx=10, pady=5)
        f.pack(side="left")
        l1 = tk.Label(f, text="UTC", font=F("titre", 9, "bold"), fg=UTC_COUL, bg=PANNEAU)
        self.c_utc = Afficheur(f, UTC_COUL, 20, secondes=True)
        sep = tk.Frame(f, bg=BORD, width=1, height=22)
        self.c_loc = Afficheur(f, ACCENT, 13, secondes=False)
        self.c_qth = tk.Label(f, text="", font=F("txt", 12), fg=ACCENT, bg=PANNEAU)
        l1.pack(side="left", padx=(0, 8))
        self.c_utc.pack(side="left")
        sep.pack(side="left", padx=12)
        self.c_loc.pack(side="left")
        self.c_qth.pack(side="left", padx=(8, 0))

        pos = self.cfg.get("compact_pos")
        if pos:
            c.geometry(f"+{pos[0]}+{pos[1]}")
        else:
            c.update_idletasks()
            c.geometry(f"+{c.winfo_screenwidth() - 340}+{40}")

        def debut(e):
            c._dx, c._dy = e.x_root - c.winfo_x(), e.y_root - c.winfo_y()

        def bouge(e):
            c.geometry(f"+{e.x_root - c._dx}+{e.y_root - c._dy}")

        def fin(e):
            self.cfg["compact_pos"] = [c.winfo_x(), c.winfo_y()]
            self.sauver()

        def menu(e):
            m = tk.Menu(c, tearoff=0)
            m.add_command(label="Fenêtre complète", command=self.fermer_compact)
            m.add_separator()
            m.add_command(label="Quitter", command=self.quitter)
            m.tk_popup(e.x_root, e.y_root)

        for w in (c, corps, bande, f, l1, self.c_utc, sep, self.c_loc, self.c_qth):
            w.bind("<ButtonPress-1>", debut)
            w.bind("<B1-Motion>", bouge)
            w.bind("<ButtonRelease-1>", fin)
            w.bind("<Double-Button-1>", lambda e: self.fermer_compact())
            w.bind("<Button-3>", menu)
        self.compact = c
        self._derniere_seconde = None

    def fermer_compact(self):
        if self.compact:
            self.compact.destroy()
            self.compact = None
        self.deiconify()
        self.afficher_vue(getattr(self, "vue_avant_compact", "villes"))

    # ------------------------------------------------------------ réglages
    def dialogue_reglages(self):
        d = tk.Toplevel(self)
        d.title("Réglages")
        d.configure(bg=FOND, padx=20, pady=16)
        d.transient(self)
        barre_titre_sombre(d)
        d.grab_set()

        tk.Label(d, text="Indicatif", bg=FOND, fg=TEXTE_DIM,
                 font=F("txt", 9)).grid(row=0, column=0, sticky="w", padx=(0, 12))
        e_ind = style_entree(tk.Entry(d, width=14))
        e_ind.insert(0, self.cfg.get("indicatif", ""))
        e_ind.grid(row=0, column=1, sticky="w", pady=4, ipady=3)
        tk.Label(d, text="Locator (QTH)", bg=FOND, fg=TEXTE_DIM,
                 font=F("txt", 9)).grid(row=1, column=0, sticky="w", padx=(0, 12))
        e_loc = style_entree(tk.Entry(d, width=14))
        e_loc.insert(0, self.cfg.get("locator", ""))
        e_loc.grid(row=1, column=1, sticky="w", pady=4, ipady=3)

        v_dem = tk.BooleanVar(value=demarrage_actif())
        cb = Bascule(d, "Démarrer avec Windows", v_dem)
        cb.grid(row=2, column=0, columnspan=2, sticky="w", pady=(14, 0))
        if os.name != "nt":
            cb.lb.configure(text="Démarrer avec Windows (Windows uniquement)")
        tk.Label(d, text="L'horloge rouvre dans la dernière vue utilisée (ex. Compact).",
                 bg=FOND, fg=TEXTE_DIM, font=F("txt", 8)).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))

        def valider():
            loc = e_loc.get().strip().upper()
            if loc and not LOCATOR_RE.match(loc):
                messagebox.showerror("Locator", "Locator invalide (ex. IN98QR).", parent=d)
                return
            self.cfg["indicatif"] = e_ind.get().strip().upper()
            self.cfg["locator"] = loc
            self.maj_qth()
            if os.name == "nt" and v_dem.get() != demarrage_actif():
                try:
                    regler_demarrage(v_dem.get())
                except Exception as ex:
                    messagebox.showerror("Démarrage", f"Impossible de régler le démarrage :\n{ex}",
                                         parent=d)
            self.sauver()
            self._jour_lever = None
            self.maj_tableau()
            if self.vue == "carte":
                self.dessiner_carte()
            d.destroy()

        self.bouton(d, "Enregistrer", valider, primaire=True).grid(row=4, column=1, sticky="e", pady=(16, 0))
        d.bind("<Return>", lambda e: valider())

    # ------------------------------------------------------------ boucle
    def maj_qth_entete(self, now, sol, loc):
        if not self.qth:
            for l in (self.l_qth_titre, self.l_qth_loc, self.l_qth_icone, self.l_qth_soleil,
                      self.l_qth_hauteur):
                l.configure(text="")
            self.l_qth_lever.configure(text="Indique ton locator dans ⚙ Réglages")
            return
        h = hauteur_soleil(self.qth[0], self.qth[1], sol)
        etat = etat_soleil(h)
        coul = COULEURS_ETAT[etat]
        self.l_qth_titre.configure(text=self.cfg.get("indicatif", "") or "QTH")
        self.l_qth_loc.configure(text=self.cfg.get("locator", "").upper())
        self.l_qth_icone.configure(text=ICONES_ETAT[etat], fg=coul)
        self.l_qth_soleil.configure(text=etat.capitalize(), fg=coul)
        self.l_qth_hauteur.configure(text=f"soleil à {h:+.0f}° au QTH")
        jour = loc.date()
        if self._jour_lever != jour:
            self._jour_lever = jour
            minuit = loc.replace(hour=0, minute=0, second=0, microsecond=0)
            lev, cou = lever_coucher(self.qth[0], self.qth[1], minuit)
            f = (lambda t: t.astimezone().strftime("%H:%M") if t else "--:--")
            self.l_qth_lever.configure(text=f"↑ lever {f(lev)}     ↓ coucher {f(cou)}")

    def tick(self):
        now = datetime.now(timezone.utc)
        if self._prop_nouvelles is not None:
            res, self._prop_nouvelles = self._prop_nouvelles, None
            self.integrer_donnees(res)
        if time.time() - self._prop_derniere > PERIODE_DONNEES:
            self.lancer_maj_donnees()
        if now.second != self._derniere_seconde:
            self._derniere_seconde = now.second
            sol = soleil(now)
            loc = now.astimezone()
            if self.compact:
                self.c_utc.regler(now.hour, now.minute, now.second)
                self.c_loc.regler(loc.hour, loc.minute)
                if self.qth:
                    e = etat_soleil(hauteur_soleil(self.qth[0], self.qth[1], sol))
                    self.c_qth.configure(text={"jour": "☀", "grayline": "◐"}.get(e, "☾"),
                                         fg=ACCENT if e in ("jour", "grayline") else LUNE)
            else:
                self.aff_utc.regler(now.hour, now.minute, now.second)
                self.l_utc_date.configure(text=f"{fmt_date(now)} {now.year}")
                self.aff_loc.regler(loc.hour, loc.minute, loc.second)
                self.l_loc_date.configure(text=f"{fmt_date(loc)} {loc.year}  ·  {fmt_offset(loc)}")
                self.maj_qth_entete(now, sol, loc)
                if self.vue == "villes":
                    for c in self.cartes:
                        c.maj(now, sol)
                elif self.vue == "carte" and \
                        (now.hour, now.minute) != self._derniere_minute_carte:
                    self.dessiner_carte()
        self.after(200, self.tick)


# ---------------------------------------------------------------- fuseaux horaires
def _fuseaux_ok():
    try:
        ZoneInfo("Europe/Paris")
        return True
    except ZoneInfoNotFoundError:
        return False


def _installer_tzdata():
    """Installe le paquet tzdata avec le Python qui exécute ce programme."""
    import subprocess
    import importlib

    exe = sys.executable
    if exe.lower().endswith("pythonw.exe"):
        exe = exe[:-len("pythonw.exe")] + "python.exe"
    flags = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW
    for opts in (["--user"], []):
        try:
            subprocess.run([exe, "-m", "pip", "install", *opts, "tzdata"],
                           check=True, capture_output=True, creationflags=flags)
            break
        except Exception:
            continue
    else:
        return False
    importlib.invalidate_caches()
    try:
        import site
        if site.ENABLE_USER_SITE and site.getusersitepackages() not in sys.path:
            sys.path.append(site.getusersitepackages())
    except Exception:
        pass
    ZoneInfo.clear_cache()
    return _fuseaux_ok()


def verifier_fuseaux():
    if _fuseaux_ok():
        return True
    ok = False
    if not GELE:
        r = tk.Tk()
        r.title(APP)
        r.configure(bg=FOND, padx=30, pady=20)
        tk.Label(r, text="Installation de la base des fuseaux horaires…\n(une seule fois)",
                 bg=FOND, fg=TEXTE, font=("Segoe UI", 11)).pack()
        barre_titre_sombre(r)
        r.update()
        ok = _installer_tzdata()
        r.destroy()
    if not ok:
        r = tk.Tk()
        r.withdraw()
        messagebox.showerror(
            "Fuseaux horaires manquants",
            "La base des fuseaux horaires est absente et l'installation\n"
            "automatique a échoué (pas d'Internet ?).\n\n"
            "Ouvre une invite de commandes et tape :\n\n"
            "    py -m pip install tzdata\n\n"
            "puis relance le programme.")
        r.destroy()
    return ok


if __name__ == "__main__":
    if verifier_fuseaux():
        App().mainloop()
