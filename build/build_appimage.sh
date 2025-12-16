#!/usr/bin/env bash
set -e

APP=CreativeSuite
APPDIR="$PWD/$APP.AppDir"

rm -rf "$APPDIR"

mkdir -p \
  "$APPDIR/usr/bin" \
  "$APPDIR/usr/share/creative-suite"

# Copy AppImage files
cp AppRun "$APPDIR/"
cp creative-suite.desktop "$APPDIR/"
cp ../assets/icons/suite-icons/lss-logo-transparent-bg.png "$APPDIR/creative-suite.png"

# Copy launcher
cp creative-suite-launcher.sh "$APPDIR/usr/bin/creative-suite"
chmod +x "$APPDIR/usr/bin/creative-suite"

# Copy app source
cp -r ../src "$APPDIR/usr/share/creative-suite/"
cp -r ../assets "$APPDIR/usr/share/creative-suite/"
cp requirements.txt "$APPDIR/usr/share/creative-suite/"

# Download appimagetool if missing
if [ ! -f appimagetool ]; then
  wget https://github.com/AppImage/AppImageKit/releases/latest/download/appimagetool-x86_64.AppImage
  chmod +x appimagetool-x86_64.AppImage
  mv appimagetool-x86_64.AppImage appimagetool
fi

# Build AppImage
ARCH=x86_64 ./appimagetool "$APPDIR"

