#!/usr/bin/env bash
#
# Dell G15 AlienFX Keyboard RGB Installer
# For Dell G15 5515 / 5520 Gaming Laptops with Alienware AW-ELC (187c:0550)
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
LIB_DIR="$HOME/.local/lib/dell_g15_rgb"
APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
AUTOSTART_DIR="$HOME/.config/autostart"

echo "=========================================================="
echo "    Dell G15 AlienFX Keyboard RGB Controller Installer    "
echo "=========================================================="
echo ""

# 1. Check Python and dependencies
echo "[1/6] Checking system dependencies..."
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 is required. Please install python3."
    exit 1
fi

# 2. Create directories
echo "[2/6] Preparing installation directories..."
mkdir -p "$BIN_DIR" "$LIB_DIR" "$APPS_DIR" "$ICONS_DIR" "$AUTOSTART_DIR"

# 3. Copy files
echo "[3/6] Installing driver, CLI, and GUI applications..."
cp -p "$SCRIPT_DIR/lib/dell_g15_rgb/__init__.py" "$LIB_DIR/"
cp -p "$SCRIPT_DIR/lib/dell_g15_rgb/controller.py" "$LIB_DIR/"
cp -p "$SCRIPT_DIR/bin/dell-rgb" "$BIN_DIR/"
cp -p "$SCRIPT_DIR/bin/dell-g15-rgb-gui" "$BIN_DIR/"
chmod +x "$BIN_DIR/dell-rgb" "$BIN_DIR/dell-g15-rgb-gui"

# 4. Desktop entry and Icon
echo "[4/6] Installing desktop launcher and app icon..."
cp -p "$SCRIPT_DIR/assets/dell-g15-rgb.svg" "$ICONS_DIR/"
cp -p "$SCRIPT_DIR/assets/dell-g15-rgb.desktop" "$APPS_DIR/"
cp -p "$SCRIPT_DIR/assets/dell-g15-rgb-restore.desktop" "$AUTOSTART_DIR/"

# Update desktop & icon caches if available
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

# 5. udev Rules & SMBIOS protection
echo "[5/6] Setting up hardware permissions (requires sudo)..."
sudo cp "$SCRIPT_DIR/udev/99-dell-alienfx-rgb.rules" /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger

# Prevent SMBIOS writes that lock the controller into red safe-mode
echo "Masking dangerous SMBIOS keyboard backlight service..."
sudo systemctl mask "systemd-backlight@leds:dell::kbd_backlight.service" 2>/dev/null || true

# 6. Apply initial state / restore
echo "[6/6] Restoring RGB profile..."
"$BIN_DIR/dell-rgb" restore || "$BIN_DIR/dell-rgb" static 0088ff || true

echo ""
echo "=========================================================="
echo "               Installation Complete!                     "
echo "=========================================================="
echo ""
echo "You can now control your keyboard RGB lighting:"
echo "  • Open the app menu and search for: 'Dell G15 Keyboard RGB'"
echo "  • Or run in terminal: dell-rgb gui"
echo "  • Or use CLI commands: dell-rgb static 0088ff"
echo "                         dell-rgb rainbow"
echo "                         dell-rgb zones ff0000 00ff00 0000ff ffff00"
echo ""
