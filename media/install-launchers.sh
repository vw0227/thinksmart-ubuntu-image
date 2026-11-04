#!/bin/sh
# Install only launchers, not applications or user configurations. No service restart.
set -eu
cd "$(dirname "$0")/.."
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
backup=$(mktemp -d /var/backups/thinksmart-media.XXXXXX)
chmod 700 "$backup"
desktop=/home/ubuntu/.local/share/applications
install -d -o ubuntu -g ubuntu "$desktop"
for name in thinksmart-bilibili thinksmart-lx-music; do
    [ ! -e "/usr/local/bin/$name" ] || cp -p "/usr/local/bin/$name" "$backup/$name"
    install -m 755 "media/$name" /usr/local/bin/
done
for name in bilibili lx-music-desktop; do
    [ ! -e "$desktop/$name.desktop" ] || cp -p "$desktop/$name.desktop" "$backup/$name.desktop"
    install -o ubuntu -g ubuntu -m 644 "media/$name.desktop" "$desktop/"
done
echo "Launchers installed. Previous files: $backup. Application packages must be installed separately."
