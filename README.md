# DogeSolo — Miner en solitari de Dogecoin 🐕

[![Llicència GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Versió](https://img.shields.io/github/v/release/jpuigbert/Doge-solo)](https://github.com/jpuigbert/Doge-solo/releases)
[![Platform](https://img.shields.io/badge/platform-linux--64%20%7C%20win--64%20%7C%20macos--64-lightgrey)](https://github.com/jpuigbert/Doge-solo/releases)

**DogeSolo** és un programa de mineria en solitari per a Dogecoin amb interfície gràfica.  
Està dissenyat perquè qualsevol persona pugui minar DOGE directament des del seu ordinador, sense necessitat de pools ni de coneixements tècnics avançats.

👉 **Si trobes un bloc, la recompensa és tota per a tu!** (només es descompta un 1% per al manteniment del projecte).

![Captura de pantalla](https://via.placeholder.com/800x450.png?text=DogeSolo+Interface)  
*(Posa aquí una captura real de l'aplicació)*

---

## ✨ Característiques principals

- ⛏️ **Mineria Scrypt nativa** — utilitza la teva CPU (suport multi‑fil).
- 🖥️ **Interfície gràfica moderna** — pestanyes per a node, mineria, cartera i configuració.
- 🤖 **Node Dogecoin Core integrat** — descàrrega automàtica, inici, aturada i seguiment de la sincronització.
- 💰 **Cartera integrada** — consulta el saldo, envia DOGE, historial de transaccions.
- 📊 **Estadístiques en temps real** — hashrate, shares, blocs trobats i gràfica de rendiment.
- 🧠 **Detecció d'inactivitat** — el miner es posa en segon pla quan l'ordinador està en ús.
- 🌗 **Tema fosc/clar automàtic** — s'adapta a la configuració del sistema.
- 📦 **Multiplataforma** — Linux (Debian/Ubuntu), Windows i macOS.

---

## 📥 Instal·lació

### 🐧 Linux (Debian / Ubuntu / Mint)

Descarrega el fitxer `.deb` de l'[última release](https://github.com/jpuigbert/Doge-solo/releases) i instal·la’l:

```bash
wget https://github.com/jpuigbert/Doge-solo/releases/download/v1.0.0/dogesolo_1.0.0_amd64.deb
sudo dpkg -i dogesolo_1.0.0_amd64.deb
sudo apt-get install -f   # si hi ha dependències
```

Després de la instal·lació, trobaràs **DogeSolo** al menú d’aplicacions (categoria *Finances* o *Utilitats*). També el pots executar des del terminal amb la comanda `dogesolo`.

### 🪟 Windows / 🍏 macOS

**No hi ha instal·ladors precompilats** en aquesta release, però pots generar el teu propi executable o bundle fàcilment amb els scripts que inclou el codi font (requereix Python 3.10+).

#### Generar l’executable per a Windows

1. Clona el repositori:
   ```bash
   git clone https://github.com/jpuigbert/Doge-solo.git
   cd Doge-solo
   ```
2. Instal·la les dependències:
   ```bash
   pip install -r requirements.txt
   ```
3. Executa el script de compilació:
   ```bash
   python build.py
   ```
   Això crearà `dist/DogeSolo.exe`.
4. (Opcional) Per crear un instal·lador MSI/Setup, utilitza l’script d’Inno Setup que trobaràs a `installers/windows/installer_script.iss`.

#### Generar el bundle per a macOS

1. Clona el repositori i instal·la les dependències (com a Windows).
2. Executa `python build.py`; es generarà `dist/DogeSolo.app`.
3. Per crear un fitxer DMG professional:
   ```bash
   cd installers/macos
   ./create_dmg.sh
   ```
   Necessitaràs tenir instal·lat `create-dmg` (`brew install create-dmg`).

---

## 🚀 Ús ràpid

1. Obre **DogeSolo**.
2. A la pestanya **Node**, prem **Instal·lar node** (descarrega Dogecoin Core automàticament) i després **Iniciar node**.
3. Espera que el node se sincronitzi amb la xarxa (pot trigar hores/dies, necessita ~60 GB d’espai).
4. A la pestanya **Mineria**, introdueix la teva adreça Dogecoin (comença per 'D') i prem **COMENÇAR A MINAR**.
5. Veuràs l’hashrate i les estadístiques en temps real.

Més informació a la [**Wiki**](https://github.com/jpuigbert/Doge-solo/wiki).

---

## 🛠️ Compilació des del codi font (totes les plataformes)

Si vols executar el programa directament sense instal·lar (o desenvolupar-hi):

```bash
git clone https://github.com/jpuigbert/Doge-solo.git
cd Doge-solo
pip install -r requirements.txt
python src/main.py
```

Per crear un executable únic amb PyInstaller:
```bash
python build.py
```

---

## 📁 Estructura del projecte

```
DogeSolo/
├── build.py                    # Script de compilació (PyInstaller)
├── requirements.txt            # Dependències Python
├── setup.py                    # Fitxer setup per a setuptools
├── src/
│   ├── main.py                 # Punt d'entrada
│   ├── core/                   # Lògica de negoci (node, miner, cartera)
│   ├── gui/                    # Interfície gràfica (pestanyes, estils)
│   └── utils/                  # Utilitats (config, logger, downloader)
└── installers/                 # Scripts per crear paquets
    ├── linux/create_deb.sh     # Genera paquet .deb
    ├── windows/installer_script.iss
    └── macos/create_dmg.sh
```

---

## 🤝 Contribucions

Tota ajuda és benvinguda!  
- Obre un [issue](https://github.com/jpuigbert/Doge-solo/issues) per reportar errors o suggerir millores.
- Fes un fork i envia un pull request.
- Comparteix el projecte amb altres miners.

---

## 📄 Llicència

Aquest projecte està llicenciat sota la **GNU General Public License v3.0**.  
Consulta el fitxer [LICENSE](https://github.com/jpuigbert/Doge-solo/blob/main/LICENSE) per a més detalls.

---

## 🐕 To the moon! 🌕

Gràcies per donar suport a DogeSolo i a la xarxa Dogecoin.  
Que la força (i els Doges) estigui amb tu!

**Much wow!** 🚀
