#!/usr/bin/env bash
#
# Dell G15 AlienFX Keyboard RGB Uninstaller
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Uninstalling Dell G15 AlienFX Keyboard RGB..."

rm -f "$HOME/.local/bin/dell-rgb"
rm -f "$HOME/.local/bin/dell-g15-rgb-gui"
rm -rf "$HOME/.local/lib/dell_g15_rgb"
rm -f "$HOME/.local/share/applications/dell-g15-rgb.desktop"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/dell-g15-rgb.svg"
rm -f "$HOME/.config/autostart/dell-g15-rgb-restore.desktop"

if [ -f "/etc/udev/rules.d/99-dell-alienfx-rgb.rules" ]; then
    echo "Removing udev rule (requires sudo)..."
    sudo rm -f "/etc/udev/rules.d/99-dell-alienfx-rgb.rules"
    sudo udevadm control --reload-rules
    sudo udevadm trigger
fi

if command -v poetry &>/dev/null && [ -d "$SCRIPT_DIR" ]; then
    echo "Cleaning up Poetry environment..."
    (cd "$SCRIPT_DIR" && poetry env remove --all 2>/dev/null || true)
fi

echo "Dell G15 Keyboard RGB has been uninstalled."
