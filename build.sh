#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$PROJECT_DIR"

# Show usage help if no argument or invalid argument is provided
usage() {
    echo "Usage: $0 {web|apk|linux|image}"
    echo "  web   - Run the Flet web app (flet run main.py -w)"
    echo "  apk   - Build Android APKs (--split-per-abi)"
    echo "  linux - Build the Linux application (flet build linux)"
    echo "  image - Build the AppImage package (automatically runs 'linux' build first)"
    exit 1
}

[[ $# -eq 1 ]] || usage

ACTION="$1"

case "$ACTION" in
    web)
        echo "Running Flet web app..."
        exec flet run main.py -w
        ;;
    apk)
        echo "Building Android APKs..."
        exec flet build apk --split-per-abi
        ;;
    linux)
        echo "Building Linux app..."
        exec flet build linux
        ;;
    image)
        echo "Ensuring Linux build is up to date..."
        flet build linux
        ;;
    *)
        echo "Error: Unknown action '$ACTION'"
        usage
        ;;
esac

# --- AppImage Generation Logic ---
BUILD_DIR="$PROJECT_DIR/build"
BUNDLE="$BUILD_DIR/linux"

CONFIG=$(python3 - <<'PY'
import tomllib
from pathlib import Path

with Path("pyproject.toml").open("rb") as f:
    config = tomllib.load(f)

project = config["project"]
flet = config["tool"]["flet"]

print(project["name"])
print(f'{flet["org"]}.{project["name"]}')
print(project["version"])
PY
)

mapfile -t CONFIG_VALUES <<< "$CONFIG"
APP="${CONFIG_VALUES[0]}"
ID="${CONFIG_VALUES[1]}"
VERSION="${CONFIG_VALUES[2]}"

APPDIR="$BUILD_DIR/${APP}.AppDir"
ARCH=$(uname -m)
APPIMAGETOOL="$BUILD_DIR/appimagetool-$ARCH.AppImage"
OUTPUT="$BUILD_DIR/${APP}-${VERSION}-${ARCH}.AppImage"

mkdir -p "$BUILD_DIR"

test -x "$BUNDLE/$APP" || {
    echo "Error: executable not found: $BUNDLE/$APP"
    echo "Build the Linux app first with: flet build linux"
    exit 1
}

DESKTOP="$BUNDLE/share/applications/$ID.desktop"
test -f "$DESKTOP" || {
    echo "Error: desktop entry not found: $DESKTOP"
    exit 1
}

# Prefer the app's custom icon over the one generated in the Flet bundle.
if [[ -f "$PROJECT_DIR/assets/icon_linux.png" ]]; then
    ICON_SRC="$PROJECT_DIR/assets/icon_linux.png"
elif [[ -f "$PROJECT_DIR/assets/icon.png" ]]; then
    ICON_SRC="$PROJECT_DIR/assets/icon.png"
else
    ICON_SRC=$(find "$BUNDLE/share/icons/hicolor" \
        -type f -name "$ID.png" -print -quit)
fi

test -n "$ICON_SRC" && test -f "$ICON_SRC" || {
    echo "Error: no PNG app icon found."
    exit 1
}

GENERATED_ICON=$(find "$BUNDLE/share/icons/hicolor" \
    -type f -name "$ID.png" -print -quit)
test -n "$GENERATED_ICON" || {
    echo "Error: Flet-generated icon not found in $BUNDLE/share/icons/hicolor"
    exit 1
}

ICON_SIZE=$(basename "$(dirname "$(dirname "$GENERATED_ICON")")")

if [[ ! -e "$APPIMAGETOOL" ]]; then
    echo "Downloading appimagetool..."
    wget -O "$APPIMAGETOOL.part" \
        "https://github.com/AppImage/appimagetool/releases/download/1.9.1/appimagetool-$ARCH.AppImage"
    mv "$APPIMAGETOOL.part" "$APPIMAGETOOL"
fi
chmod +x "$APPIMAGETOOL"

rm -rf -- "$APPDIR"
mkdir -p \
    "$APPDIR/usr/bin" \
    "$APPDIR/usr/share/applications" \
    "$APPDIR/usr/share/icons/hicolor/$ICON_SIZE/apps"

cp -a "$BUNDLE"/. "$APPDIR/usr/bin/"
rm -rf -- "$APPDIR/usr/bin/share"

cp "$DESKTOP" "$APPDIR/usr/share/applications/$ID.desktop"
cp "$ICON_SRC" "$APPDIR/usr/share/icons/hicolor/$ICON_SIZE/apps/$ID.png"
cp "$ICON_SRC" "$APPDIR/$ID.png"

sed -i \
    -e "s|^Exec=.*|Exec=$APP|" \
    -e "s|^Icon=.*|Icon=$ID|" \
    "$APPDIR/usr/share/applications/$ID.desktop"

if ! grep -q '^Icon=' "$APPDIR/usr/share/applications/$ID.desktop"; then
    printf '\nIcon=%s\n' "$ID" >> "$APPDIR/usr/share/applications/$ID.desktop"
fi

ln -s "usr/share/applications/$ID.desktop" "$APPDIR/$ID.desktop"
ln -s "$ID.png" "$APPDIR/.DirIcon"

printf '#!/bin/sh\nHERE=$(dirname "$(readlink -f "$0")")\nexec "$HERE/usr/bin/%s" "$@"\n' \
    "$APP" > "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"

rm -f -- "$OUTPUT"
APPIMAGE_EXTRACT_AND_RUN=1 VERSION="$VERSION" \
    "$APPIMAGETOOL" --no-appstream "$APPDIR" "$OUTPUT"

echo "AppImage created: $OUTPUT"