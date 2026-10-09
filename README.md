# Horloge mondiale F4GOP

Horloge mondiale pour la station radioamateur, sur PC Windows : heure UTC et locale,
fuseaux des pays, carte grayline et conditions de propagation HF en direct.

![Vue Pays](docs/pays.png)

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
- **Mode compact** : petite bande UTC toujours au premier plan, déplaçable.
- **Démarrage avec Windows** (option dans les réglages).

![Vue Carte](docs/carte.png)

*Capture réalisée avec des données de propagation simulées.*

![Mode compact](docs/compact.png)

## Installation

### Le plus simple : l'exécutable

Télécharger `HorlogeMondiale.exe` dans la page **Releases** du dépôt et le lancer.
Rien d'autre à installer.

### Depuis le code Python

Python 3.9 ou plus récent. Sous Windows :

```
py -m pip install tzdata
py horloge_mondiale.py
```

Le module `tzdata` est installé automatiquement au premier lancement s'il manque.
Renommer le fichier en `horloge_mondiale.pyw` évite la fenêtre console.

### Construire l'exécutable soi-même

Double-cliquer sur `construire_exe.bat` (installe PyInstaller et produit
`HorlogeMondiale.exe`).

## Premier lancement

Ouvrir **⚙ Réglages** pour indiquer son **indicatif** et son **locator** : ils servent
au panneau QTH, aux distances/azimuts et au choix de l'ionosonde la plus proche.

Les réglages sont enregistrés dans `horloge_mondiale.json`, dans le dossier utilisateur.

## Sources des données

- Indices solaires et conditions de bandes : [N0NBH — hamqsl.com](https://www.hamqsl.com/solar.html)
- MUF et ionosondes : [KC2G — prop.kc2g.com](https://prop.kc2g.com/) (données GIRO)
- Ovale auroral : [NOAA SWPC — modèle OVATION](https://www.swpc.noaa.gov/products/aurora-30-minute-forecast)
- Contours des terres : paquet Python `global-land-mask` (données NOAA GLOBE)

Merci à ces services de mettre leurs données à disposition de la communauté.

## Licence

MIT — voir [LICENSE](LICENSE).

73 de F4GOP
