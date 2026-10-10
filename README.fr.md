# Horloge mondiale F4GOP

🇬🇧 [English version](README.md)

Horloge mondiale pour la station radioamateur, sur PC Windows : heure UTC et locale,
fuseaux des pays, carte grayline et conditions de propagation HF en direct.

**Disponible en 6 langues :** français, English, Español, Deutsch, Italiano, Português
(détectée automatiquement d'après Windows, modifiable dans ⚙ Réglages).

![Vue Pays](pays.png)

## Fonctions

- **UTC et heure locale** en grand, avec le lever et le coucher du soleil au QTH.
- **Pays du monde** : heure, date et décalage UTC. Chaque carte montre si le pays est
  en jour, en grayline ou en nuit (calcul solaire réel) et une barre jour/nuit sur 24 h.
  Ajout par recherche (« italie », « canada »…), suppression par clic droit.
- **Carte grayline** : jour/nuit, terminateur, QTH et pays affichés. Au survol :
  locator, distance, azimut depuis le QTH et hauteur du soleil.
- **Propagation** (mise à jour toutes les 15 min) :
  - courbes de **MUF(3000)** et mesures des **ionosondes** ;
  - **ovale auroral** ;
  - **indices** SFI, SSN, A, K, rayons X, vent solaire, Bz, géomagnétisme, bruit ;
  - **bandes HF** jour/nuit et conditions **VHF** (Es, aurore) ;
  - MUF de l'ionosonde la plus proche du QTH.
- **DX cluster** (nouveau en 1.3) : spots DX en direct reçus par telnet (connexion avec ton
  indicatif), affichés sur les cartes et dans une liste avec fréquence, pays, distance et azimut ;
  filtre par bande.
- **Carte azimutale centrée sur le QTH** (nouveau en 1.3) : direction et distance réelles de chaque
  spot et pays, cercles de distance, grayline. Un clic sur un spot trace son trajet grand cercle.
- **Alertes DX** (nouveau en 1.5) : son et fenêtre d'alerte quand un indicatif, un préfixe ou
  un pays surveillé est spotté, ou quand apparaît un pays DXCC jamais contacté (ou une nouvelle bande).
- **Pays manquants d'après ton log** (nouveau en 1.5) : importe ton log ADIF ; les spots sont
  marqués **NEW** (jamais contacté) ou **BAND** (nouvelle bande). Le log est relu automatiquement
  quand ton logiciel de log le met à jour.
- **Lune / EME** (nouveau en 1.5) : phase, hauteur et azimut de la Lune au QTH, lever/coucher,
  distance ; fenêtres EME communes avec un autre locator sur 48 h, avec courbe de hauteur sur 24 h.
- **Avis de mise à jour** (nouveau en 1.5) : un bandeau s'affiche quand une nouvelle version est
  publiée sur GitHub.
- **Pilotage du poste et du rotor** (nouveau en 1.6) : un double-clic sur un spot accorde le poste
  (fréquence et mode) et tourne l'antenne vers le DX. Le poste est commandé via le partage CAT de
  ton logiciel de log en **Hamlib NET rigctl** (OpsLog, Log4OM…, par défaut `127.0.0.1:4532`) :
  aucun conflit de port COM. Le rotor passe par **PST Rotator** en UDP (`127.0.0.1:12000`) ou
  directement par un contrôleur **GS-232A** en TCP.
- **Vues du panneau DX** (nouveau en 2.0) : **Spots**, **Activité** (spots par bande et continent
  du DX sur les 30 dernières minutes) et **Concours** (concours de la semaine d'après le calendrier
  WA7BNM, ceux en cours mis en avant avec le temps restant).
- **Filtres par mode et skimmers** (nouveau en 2.0) : Tous / CW / Digi / Phonie, et spots CW Skimmer
  (RBN) affichés, masqués ou limités à ≥ 10 dB.
- **Taille d'affichage** (nouveau en 2.0) : 100 %, 125 % ou 150 % pour les grands écrans de station.
- **Mode compact** : petite bande UTC toujours au premier plan, déplaçable.
- **Démarrage avec Windows** (option dans les réglages).

![Vue Carte](carte.png)

![Vue DX](dx_fr.png)

![Vue Lune / EME](lune.png)

*Capture réalisée avec des données de propagation simulées.*

![Mode compact](compact.png)

## Installation

### Le plus simple : l'exécutable

**[⬇ Télécharger HorlogeMondiale.exe](https://github.com/f4gopdenis-cyber/horloge-mondiale/releases/latest/download/HorlogeMondiale.exe)**
(dernière version), puis le lancer. Rien d'autre à installer.

Toutes les versions : [page des Releases](https://github.com/f4gopdenis-cyber/horloge-mondiale/releases)

> **Note :** au premier lancement, Windows peut afficher « Windows a protégé votre
> ordinateur » (SmartScreen), car l'exécutable n'est pas signé. Cliquer sur
> **Informations complémentaires** puis **Exécuter quand même**. Le code source
> complet est disponible dans ce dépôt, et l'exécutable est compilé automatiquement
> par GitHub Actions à partir de ce code.

### Depuis le code Python

Python 3.9 ou plus récent. Sous Windows :

    py -m pip install tzdata
    py horloge_mondiale.py

Le module `tzdata` est installé automatiquement au premier lancement s'il manque.
Renommer le fichier en `horloge_mondiale.pyw` évite la fenêtre console.

### Construire l'exécutable soi-même

Double-cliquer sur `construire_exe.bat` (installe PyInstaller et produit
`HorlogeMondiale.exe`).

## Premier lancement

La fenêtre **⚙ Réglages** s'ouvre automatiquement : choisir la langue, puis indiquer
son **indicatif** et son **locator**. Ils servent au panneau QTH, aux distances/azimuts,
à la carte azimutale, au choix de l'ionosonde la plus proche et à la connexion au DX cluster.
Le serveur du cluster se change dans les réglages (par défaut, connexion **simultanée** à EA4RCH, F5MZN, N8DXE, WA9PIE et VE7CC pour des spots plus rapides ; les doublons sont fusionnés).

Les réglages sont enregistrés dans `horloge_mondiale.json`, dans le dossier utilisateur.

## Sources des données

- Indices solaires et conditions de bandes : [N0NBH — hamqsl.com](https://www.hamqsl.com/solar.html)
- MUF et ionosondes : [KC2G — prop.kc2g.com](https://prop.kc2g.com/) (données GIRO)
- Ovale auroral : [NOAA SWPC — modèle OVATION](https://www.swpc.noaa.gov/products/aurora-30-minute-forecast)
- Préfixes DXCC : [fichiers pays d'AD1C — cty.dat](https://www.country-files.com/)
- Spots DX : réseau DX cluster (nœuds EA4RCH, F5MZN, N8DXE, WA9PIE, VE7CC)
- Calendrier des concours : [WA7BNM Contest Calendar](https://www.contestcalendar.com/)
- Contours des terres : paquet Python `global-land-mask` (données NOAA GLOBE)
- Noms des pays, jours et mois : Unicode CLDR

Merci à ces services de mettre leurs données à disposition de la communauté.

## Licence

MIT — voir [LICENSE](LICENSE).

73 de F4GOP
