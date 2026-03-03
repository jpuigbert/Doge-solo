#!/bin/bash
# Crea un DMG professional per a DogeSolo en macOS
# Prerequisits: brew install create-dmg

set -e

APP_NAME="DogeSolo"
VERSION="1.0.0"
APP_BUNDLE="../../dist/${APP_NAME}.app"
DMG_OUTPUT="../../dist/${APP_NAME}-${VERSION}-macOS.dmg"
VOLUME_NAME="${APP_NAME} ${VERSION}"

# Colors per logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  Creant DMG per ${APP_NAME} v${VERSION}${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Comprovar que existeix el .app
if [ ! -d "${APP_BUNDLE}" ]; then
    echo -e "${RED}Error: No trobo ${APP_BUNDLE}${NC}"
    echo "Executa primer: python build.py"
    exit 1
fi

# Comprovar que create-dmg està instal·lat
if ! command -v create-dmg &> /dev/null; then
    echo -e "${YELLOW}Instal·lant create-dmg...${NC}"
    brew install create-dmg
fi

# Eliminar DMG anterior si existeix
rm -f "${DMG_OUTPUT}"

# Crear DMG amb estil professional
create-dmg \
    --volname "${VOLUME_NAME}" \
    --volicon "../../src/resources/icon.icns" \
    --background "../../src/resources/dmg_background.png" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "${APP_NAME}.app" 150 185 \
    --hide-extension "${APP_NAME}.app" \
    --app-drop-link 450 185 \
    --no-internet-enable \
    "${DMG_OUTPUT}" \
    "${APP_BUNDLE}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ DMG creat: ${DMG_OUTPUT}${NC}"
    
    # Mostrar mida del fitxer
    SIZE=$(du -sh "${DMG_OUTPUT}" | cut -f1)
    echo -e "${GREEN}   Mida: ${SIZE}${NC}"
else
    echo -e "${RED}❌ Error creant el DMG${NC}"
    exit 1
fi

# Opcional: notarize amb Apple (requereix Apple Developer ID)
# Si tens un compte de desenvolupador, descomenta:
# echo "Notaritzant per a Gatekeeper..."
# xcrun notarytool submit "${DMG_OUTPUT}" \
#     --apple-id "el-teu@email.com" \
#     --team-id "XXXXXXXXXX" \
#     --password "@keychain:AC_PASSWORD" \
#     --wait
# xcrun stapler staple "${DMG_OUTPUT}"

echo ""
echo -e "${GREEN}✅ Procés completat!${NC}"
echo "Distribueix: ${DMG_OUTPUT}"