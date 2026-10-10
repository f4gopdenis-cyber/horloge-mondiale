# World Clock F4GOP

🇫🇷 [Version française](README.fr.md)

World clock for the amateur radio shack, for Windows PCs: UTC and local time,
country time zones, greyline map and live HF propagation conditions.

**Available in 6 languages:** English, Français, Español, Deutsch, Italiano, Português
(detected automatically from Windows, can be changed in ⚙ Settings).

![Countries view](countries.png)

## Features

- **UTC and local time** in large digits, with sunrise and sunset at your QTH.
- **Countries of the world**: time, date and UTC offset. Each card shows whether the
  country is in daylight, greyline or night (real solar calculation) and a 24 h
  day/night bar. Add countries by searching ("italy", "canada"…), remove with a right-click.
- **Greyline map**: day/night, terminator, QTH and countries. On hover: locator,
  distance, bearing from your QTH and sun elevation.
- **Propagation** (refreshed every 15 min):
  - **MUF(3000)** contours and **ionosonde** readings;
  - **auroral oval**;
  - **indices**: SFI, SSN, A, K, X-rays, solar wind, Bz, geomagnetic field, noise;
  - **HF band conditions** day/night and **VHF** conditions (Es, aurora);
  - MUF of the ionosonde nearest to your QTH.
- **DX cluster** (new in 1.3): live DX spots received over telnet (your callsign is used to log in),
  shown on the maps and in a list with frequency, country, distance and bearing; band filter.
- **Azimuthal map centred on your QTH** (new in 1.3): true bearing and distance to every spot
  and country, distance rings, greyline. Click a spot to draw its great-circle path.
- **Compact mode**: small always-on-top UTC strip you can move anywhere.
- **Start with Windows** (option in the settings).

![Map view](map.png)

![DX view](dx.png)

*Screenshot taken with simulated propagation data.*

## Installation

### Easiest: the executable

**[⬇ Download HorlogeMondiale.exe](https://github.com/f4gopdenis-cyber/horloge-mondiale/releases/latest/download/HorlogeMondiale.exe)**
(latest version), then run it. Nothing else to install.

All versions: [Releases page](https://github.com/f4gopdenis-cyber/horloge-mondiale/releases)

> **Note:** on first launch, Windows may show "Windows protected your PC"
> (SmartScreen) because the executable is not code-signed. Click **More info**, then
> **Run anyway**. The full source code is in this repository, and the executable is
> built automatically by GitHub Actions from this code.

### From the Python source

Python 3.9 or later. On Windows:

    py -m pip install tzdata
    py horloge_mondiale.py

`tzdata` is installed automatically on first launch if it is missing.
Renaming the file to `horloge_mondiale.pyw` avoids the console window.

## First launch

The **⚙ Settings** window opens automatically: choose your language and enter your
**callsign** and **locator**. They are used for the QTH panel, distances/bearings, the
azimuthal map, the nearest ionosonde and the DX cluster login. The DX cluster server can be
changed in the settings (default `ea4rch.dxfun.com:8000`, with automatic fallback to F5MZN, N8DXE, WA9PIE and VE7CC).

Settings are saved in `horloge_mondiale.json`, in your user folder.

## Data sources

- Solar indices and band conditions: [N0NBH — hamqsl.com](https://www.hamqsl.com/solar.html)
- MUF and ionosondes: [KC2G — prop.kc2g.com](https://prop.kc2g.com/) (GIRO data)
- Auroral oval: [NOAA SWPC — OVATION model](https://www.swpc.noaa.gov/products/aurora-30-minute-forecast)
- DXCC prefixes: [AD1C country files — cty.dat](https://www.country-files.com/)
- DX spots: DX cluster network (EA4RCH, F5MZN, N8DXE, WA9PIE, VE7CC nodes)
- Land outlines: `global-land-mask` Python package (NOAA GLOBE data)
- Country, day and month names: Unicode CLDR

Many thanks to these services for sharing their data with the community.

## License

MIT — see [LICENSE](LICENSE).

73 de F4GOP
