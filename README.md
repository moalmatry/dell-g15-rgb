# Dell G15 AlienFX Keyboard RGB for Linux 🌈

Native Linux driver, CLI, and GTK 3 graphical control panel for **Dell G15 (5515 / 5520)** laptops equipped with the **Alienware AW-ELC (187c:0550)** 4-Zone RGB keyboard lighting controller.

Fixes the infamous **"stuck on red"** backlight issue on Linux without needing heavy daemons or Windows virtual machines.

---

## 🚀 Features

* **🎨 Native GTK 3 Control Panel:** Beautiful, lightweight desktop app that integrates seamlessly with GNOME, Zorin OS, and Ubuntu desktop themes.
* **⚡ Instant Terminal CLI (`dell-rgb`):** Fast command-line interface with sub-second execution and **0% background CPU/RAM usage**.
* **⌨️ 4-Zone Lighting:** Full independent RGB color picking for each of the 4 physical keyboard zones (Left, Mid-Left, Mid-Right, Right).
* **✨ Dynamic Hardware Effects:**
  * 🌈 **Rainbow Wave** (smooth color wave sweeping across the 4 zones)
  * 🔄 **Spectrum Cycle** (synchronized multi-color cycling)
  * 💓 **Pulse / Breathe** (breathing effect with adjustable speed)
  * 🔀 **Morph** (smooth transition between any two custom colors)
* **💡 Brightness & Power Control:** Full dimming control (0%–100%) and instant backlight on/off switch.
* **💾 Automatic Persistence:** Your chosen colors are saved to `~/.config/dell-g15-rgb/config.json` and automatically restored at login and boot via an XDG autostart service.
* **🔌 AC & Battery Synchronization:** Programs both the active running slot (`0xFFFF`), the persistent post-boot slot (`0x0061`), and power slots (`0x5C`, `0x5D`, `0x5F`) so your colors remain active whether plugged in or running on battery.

---

## 🔍 Why Was the Keyboard Stuck on Red?

On Linux, Dell G15 laptops with AlienFX RGB keyboards frequently get stuck on solid red due to two firmware quirks:

1. **The SMBIOS / ACPI Wedge Trigger:** Whenever Linux tools (like `systemd-backlight` or `brightnessctl`) attempt to write to `/sys/class/leds/dell::kbd_backlight` via SMBIOS, the laptop's Embedded Controller (EC) gets wedged into a safe-mode state where it ignores all color commands and stays solid red.
2. **Control Pipe vs. Interrupt Endpoints:** The AW-ELC firmware ignores USB interrupt endpoints and only responds to **USB control transfers** (`HIDIOCSOUTPUT` and `HIDIOCGINPUT` on `/dev/hidraw` with Report ID `0` and preamble `0x03`).
3. **16-Zone Architecture (G15 5515):** The 5515 Ryzen Edition reports 16 internal LED addresses (4 per physical keyboard section), requiring a specific packet mapping and dimming payload.

This project bypasses SMBIOS entirely, speaks the exact USB control pipe protocol reverse-engineered from AWCC, and permanently masks the problematic systemd-backlight writer.

---

## 💻 Supported Hardware

* **Dell G15 5515** (AMD Ryzen Edition) — Controller `187c:0550`, 16-zone platform `0x0E05`
* **Dell G15 5520** (Intel Edition) — Controller `187c:0550`, 20-zone platform `0x0E07`
* Any Dell / Alienware laptop utilizing the **AW-ELC** USB lighting controller (`187c:0550`)

---

## 📦 Installation

### Prerequisites
* Python 3 (`python3`)
* PyGObject GTK 3 (`python3-gi`, standard on Ubuntu/Debian/Zorin/Fedora)

### Install via Installer Script

```bash
git clone https://github.com/moalmatry/dell-g15-rgb.git
cd dell-g15-rgb
chmod +x install.sh
./install.sh
```

The installer will:
1. Install the `dell_g15_rgb` Python driver and `dell-rgb` CLI to `~/.local/bin/`.
2. Install the desktop launcher and icon into your application menu (**"Dell G15 Keyboard RGB"**).
3. Set up udev rules for passwordless hardware access.
4. Mask `systemd-backlight@leds:dell::kbd_backlight.service` to prevent the controller from wedging.
5. Enable the user autostart service to restore your lighting profile on login.

---

## 🖥️ Usage

### Graphical App (GUI)
Launch **"Dell G15 Keyboard RGB"** from your application menu, or run:
```bash
dell-rgb gui
```

---

### Command-Line Interface (`dell-rgb`)

#### Solid Static Color (Whole Keyboard)
```bash
dell-rgb static 00ffaa       # Vibrant Cyan / Aqua
dell-rgb static 0088ff       # Sky Blue
dell-rgb static ff0055       # Pink / Magenta
dell-rgb static 00ff00       # Emerald Green
dell-rgb static ffff00       # Electric Yellow
```

#### 4-Zone Custom Colors (Left to Right)
```bash
# Zone 1 (Left), Zone 2 (Mid-Left), Zone 3 (Mid-Right), Zone 4 (Right)
dell-rgb zones ff0000 00ff00 0000ff ffff00
```

#### Dynamic Animated Effects
```bash
# Rainbow Wave
dell-rgb rainbow --speed 5

# Spectrum Cycle
dell-rgb cycle --speed 6

# Breathing / Pulse
dell-rgb pulse 0088ff --speed 5

# Morph between two colors
dell-rgb morph ff0000 0000ff --speed 5
```

#### Brightness & Power Control
```bash
# Set brightness percentage (0 to 100)
dell-rgb brightness 75

# Turn off backlight
dell-rgb off

# Turn on backlight (restores saved profile)
dell-rgb on

# Restore saved profile manually
dell-rgb restore
```

---

## 🛠️ Uninstallation

If you ever wish to remove the software:
```bash
cd dell-g15-rgb
./uninstall.sh
```

---

## 🔧 Troubleshooting

### Controller Stuck on Red from a Previous Session?
If your controller was already wedged into red failsafe mode by an older utility or by SMBIOS writes:
1. Shut down the laptop completely.
2. Disconnect the charger.
3. Hold the **Power Button** for **30 seconds** (this resets the Dell Embedded Controller / RTC standby power rail).
4. Connect the charger and boot back into Linux.
5. Run `dell-rgb static 0088ff` to apply your desired color.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
