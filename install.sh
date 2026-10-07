#!/usr/bin/env bash
#
# Dell G15 AlienFX Keyboard RGB Installer
# For Dell G15 5515 / 5520 Gaming Laptops with Alienware AW-ELC (187c:0550)
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
AUTOSTART_DIR="$HOME/.config/autostart"

echo "=========================================================="
echo "    Dell G15 AlienFX Keyboard RGB Controller Installer    "
echo "=========================================================="
echo ""

# 1. Check Python and Poetry
echo "[1/6] Checking system dependencies..."
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 is required. Please install python3."
    exit 1
fi

if ! command -v poetry &>/dev/null; then
    echo "Error: Poetry is required but not installed."
    echo "Please install Poetry using one of the following methods:"
    echo "  • Official installer: curl -sSL https://install.python-poetry.org | python3 -"
    echo "  • Or via apt:         sudo apt install python3-poetry"
    exit 1
fi

# 2. Create directories
echo "[2/6] Preparing installation directories..."
mkdir -p "$BIN_DIR" "$APPS_DIR" "$ICONS_DIR" "$AUTOSTART_DIR"

# 3. Install Python package via Poetry
echo "[3/6] Setting up Poetry environment and installing package..."
cd "$SCRIPT_DIR"

# Allow virtualenv to access system-site-packages for PyGObject / GTK
poetry config virtualenvs.options.system-site-packages true --local 2>/dev/null || true
poetry install

VENV_PATH="$(poetry env info -p)"
if [ -z "$VENV_PATH" ] || [ ! -d "$VENV_PATH" ]; then
    echo "Error: Failed to locate Poetry virtual environment."
    exit 1
fi

ln -sf "$VENV_PATH/bin/dell-rgb" "$BIN_DIR/dell-rgb"
ln -sf "$VENV_PATH/bin/dell-g15-rgb-gui" "$BIN_DIR/dell-g15-rgb-gui"
chmod +x "$BIN_DIR/dell-rgb" "$BIN_DIR/dell-g15-rgb-gui"

# 4. Desktop entry and Icon
echo "[4/6] Installing desktop launcher and app icon..."
cp -p "$SCRIPT_DIR/assets/dell-g15-rgb.svg" "$ICONS_DIR/"
cp -p "$SCRIPT_DIR/assets/dell-g15-rgb.desktop" "$APPS_DIR/"
sed -i "s|Exec=dell-g15-rgb-gui|Exec=$BIN_DIR/dell-g15-rgb-gui|g" "$APPS_DIR/dell-g15-rgb.desktop"
cp -p "$SCRIPT_DIR/assets/dell-g15-rgb-restore.desktop" "$AUTOSTART_DIR/"
sed -i "s|Exec=dell-rgb restore|Exec=$BIN_DIR/dell-rgb restore|g" "$AUTOSTART_DIR/dell-g15-rgb-restore.desktop"

# Update desktop & icon caches if available
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

# 5. udev Rules & SMBIOS protection
echo "[5/6] Checking hardware permissions..."
if [ -f "/etc/udev/rules.d/99-dell-alienfx-rgb.rules" ] && cmp -s "$SCRIPT_DIR/udev/99-dell-alienfx-rgb.rules" "/etc/udev/rules.d/99-dell-alienfx-rgb.rules"; then
    echo "udev rule is already installed and up-to-date."
else
    echo "Installing udev rules (requires sudo)..."
    sudo cp "$SCRIPT_DIR/udev/99-dell-alienfx-rgb.rules" /etc/udev/rules.d/
    sudo udevadm control --reload-rules
    sudo udevadm trigger
fi

if systemctl is-enabled "systemd-backlight@leds:dell::kbd_backlight.service" 2>/dev/null | grep -q "masked"; then
    echo "SMBIOS keyboard backlight service is already masked."
else
    echo "Masking dangerous SMBIOS keyboard backlight service (requires sudo)..."
    sudo systemctl mask "systemd-backlight@leds:dell::kbd_backlight.service" 2>/dev/null || true
fi

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
