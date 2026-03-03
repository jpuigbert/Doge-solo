#!/bin/bash
# Crea un paquet .deb per a DogeSolo (Debian/Ubuntu/Linux Mint)
# Ús: ./create_deb.sh

set -e

APP_NAME="dogesolo"
APP_DISPLAY="DogeSolo"
VERSION="1.0.0"
ARCH="amd64"  # canvia a "arm64" per a Raspberry Pi
MAINTAINER="DogeSolo Project <info@dogesolo.org>"
DESCRIPTION="Mineria Dogecoin en solitari per a tothom"
BINARY="../../dist/DogeSolo"
DEB_OUTPUT="../../dist/${APP_NAME}_${VERSION}_${ARCH}.deb"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  Creant .deb per ${APP_DISPLAY} v${VERSION}${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ ! -f "${BINARY}" ]; then
    echo -e "${RED}Error: No trobo ${BINARY}${NC}"
    echo "Executa primer: python build.py"
    exit 1
fi

# Crear estructura del paquet Debian
PKG_DIR="/tmp/${APP_NAME}_${VERSION}"
rm -rf "${PKG_DIR}"

mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${PKG_DIR}/usr/share/doc/${APP_NAME}"

# ── Fitxer de control ──────────────────────────────────────────────────
cat > "${PKG_DIR}/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: libc6, libstdc++6
Recommends: curl
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
 DogeSolo permet minar Dogecoin de manera independent i descentralitzada
 directament des del teu ordinador, sense necessitat de pools de mineria.
 Inclou descàrrega automàtica de Dogecoin Core i interfície gràfica senzilla.
 .
 Nota: La mineria CPU és poc probable de trobar blocs a la xarxa principal,
 però és 100% descentralitzada i educativa.
EOF

# ── Scripts pre/post ───────────────────────────────────────────────────
cat > "${PKG_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e
# Crear grup per a dogesolo si no existeix
if ! getent group dogesolo > /dev/null 2>&1; then
    groupadd -r dogesolo 2>/dev/null || true
fi
# Actualitzar caché d'aplicacions
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor || true
fi
EOF
chmod 755 "${PKG_DIR}/DEBIAN/postinst"

# ── Binari executable ──────────────────────────────────────────────────
cp "${BINARY}" "${PKG_DIR}/usr/bin/${APP_NAME}"
chmod 755 "${PKG_DIR}/usr/bin/${APP_NAME}"

# ── Fitxer .desktop (entrada al menú) ─────────────────────────────────
cat > "${PKG_DIR}/usr/share/applications/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=${APP_DISPLAY}
Comment=${DESCRIPTION}
Exec=${APP_NAME}
Icon=${APP_NAME}
Categories=Office;Finance;Utility;
Terminal=false
StartupNotify=true
StartupWMClass=DogeSolo
Keywords=dogecoin;mining;crypto;blockchain;doge;
EOF

# ── Icona ──────────────────────────────────────────────────────────────
if [ -f "../../src/resources/icon.png" ]; then
    cp "../../src/resources/icon.png" \
       "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
fi

# ── Documentació ──────────────────────────────────────────────────────
cat > "${PKG_DIR}/usr/share/doc/${APP_NAME}/copyright" << EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: ${APP_DISPLAY}
Upstream-Contact: ${MAINTAINER}
Source: https://github.com/dogesolo/dogesolo

Files: *
Copyright: 2024 DogeSolo Project
License: MIT
EOF

# ── Construir el paquet ────────────────────────────────────────────────
echo -e "${YELLOW}Construint paquet .deb...${NC}"
dpkg-deb --build --root-owner-group "${PKG_DIR}" "${DEB_OUTPUT}"

if [ $? -eq 0 ]; then
    SIZE=$(du -sh "${DEB_OUTPUT}" | cut -f1)
    echo -e "${GREEN}✅ Paquet creat: ${DEB_OUTPUT}${NC}"
    echo -e "${GREEN}   Mida: ${SIZE}${NC}"
    echo ""
    echo "Per instal·lar:"
    echo -e "  ${YELLOW}sudo dpkg -i ${DEB_OUTPUT}${NC}"
    echo -e "  ${YELLOW}sudo apt-get install -f${NC}  (si hi ha dependències)"
else
    echo -e "${RED}❌ Error creant el paquet${NC}"
    exit 1
fi

# Netejar directori temporal
rm -rf "${PKG_DIR}"