"""Dell G15 Alienware AW-ELC (187c:0550) RGB LED Controller.

Provides direct USB control pipe transport with dynamic platform detection
for Dell G15 5515 (16-zone) and 5520+ (20-zone) laptops.
"""
import fcntl
import glob
import json
import os
import sys

STATE_FILE = os.path.expanduser("~/.config/dell-g15-rgb/config.json")
ZONES = [0, 1, 2, 3]

SPECTRUM = [
    (0xFF, 0x00, 0x00),  # Red
    (0xFF, 0xA5, 0x00),  # Orange
    (0xFF, 0xFF, 0x00),  # Yellow
    (0x00, 0x80, 0x00),  # Green
    (0x00, 0xBF, 0xFF),  # Deep Sky Blue
    (0x00, 0x00, 0xFF),  # Blue
    (0x80, 0x00, 0x80),  # Purple
]


def _ioc(nr):
    return (3 << 30) | (34 << 16) | (ord("H") << 8) | nr


HIDIOCGINPUT = _ioc(0x0A)
HIDIOCSOUTPUT = _ioc(0x0B)


class DellG15RGB:
    def __init__(self, dev_path=None):
        self.dev_path = dev_path or self.find_device()
        if not self.dev_path:
            raise FileNotFoundError("Dell G15 RGB controller (187c:0550) not found in /sys/class/hidraw")
        self.zone_count, self.section_zones = self._detect_platform()
        self.zones = [0, 1, 2, 3]

    @staticmethod
    def find_device():
        for uevent in sorted(glob.glob("/sys/class/hidraw/hidraw*/device/uevent")):
            try:
                with open(uevent, "r") as f:
                    content = f.read().upper()
                    if "0000187C:00000550" in content:
                        dev_name = os.path.basename(os.path.dirname(os.path.dirname(uevent)))
                        path = f"/dev/{dev_name}"
                        if os.path.exists(path):
                            return path
            except OSError:
                continue
        return None

    def _cmd(self, fd, *payload):
        buf = bytearray(34)
        data = bytes([0x03, *payload])
        buf[1 : 1 + len(data)] = data
        fcntl.ioctl(fd, HIDIOCSOUTPUT, buf)
        ack = bytearray(34)
        fcntl.ioctl(fd, HIDIOCGINPUT, ack)
        return bytes(ack[1:])

    def _detect_platform(self):
        try:
            with open(self.dev_path, "r+b", buffering=0) as f:
                ack = self._cmd(f.fileno(), 0x20, 0x02)  # GET_PLATFORM
                if len(ack) >= 6 and ack[0] == 0x20 and ack[1] == 0x02:
                    count = ack[5]
                    if count == 16:
                        # 16-zone Dell G15 5515: 4 LEDs per keyboard section
                        return 16, [
                            [0, 1, 2, 3],        # Section 1 (Left)
                            [4, 5, 6, 7],        # Section 2 (Mid-Left)
                            [8, 9, 10, 11],      # Section 3 (Mid-Right)
                            [12, 13, 14, 15],    # Section 4 (Right)
                        ]
                    elif count == 20:
                        # 20-zone Dell G15 5520+
                        return 20, [[0x10], [0x11], [0x12], [0x13]]
                    elif count > 0:
                        step = max(1, count // 4)
                        return count, [
                            list(range(0, step)),
                            list(range(step, 2 * step)),
                            list(range(2 * step, 3 * step)),
                            list(range(3 * step, count)),
                        ]
        except Exception:
            pass
        return 16, [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15]]

    def _timing(self, speed):
        s = max(1, min(10, int(speed)))
        dur = 3200 - 300 * s
        tempo = max(15, dur // 20)
        return dur, tempo

    def _dim(self, fd, brightness):
        b = max(0, min(100, int(brightness)))
        dimming = 100 - b
        payload = [0x26, dimming, 0x00, self.zone_count] + list(range(self.zone_count))
        self._cmd(fd, *payload)

    def _anim(self, fd, sub, anim_id):
        cmd_type = 0x22 if (0x5B <= anim_id <= 0x60) else 0x21
        self._cmd(fd, cmd_type, 0x00, sub, (anim_id >> 8) & 0xFF, anim_id & 0xFF)

    def _play_groups(self, fd, groups, anim_id=0xFFFF):
        is_running = (anim_id == 0xFFFF)
        # 1. Remove existing animation in this slot
        self._anim(fd, 0x04, anim_id)
        # 2. Start new animation
        self._anim(fd, 0x01, anim_id)

        # 3. Write series and actions for each zone group
        for zones, actions in groups:
            series = [0x23, 0x01, 0x00, len(zones)] + list(zones)
            self._cmd(fd, *series)
            for i in range(0, len(actions), 3):
                chunk = actions[i : i + 3]
                p = [0x24]
                for effect, dur, tempo, r, g, b in chunk:
                    p.extend([
                        effect,
                        (dur >> 8) & 0xFF,
                        dur & 0xFF,
                        (tempo >> 8) & 0xFF,
                        tempo & 0xFF,
                        r,
                        g,
                        b,
                    ])
                self._cmd(fd, *p)

        # 4. Finish and activate animation
        if is_running:
            self._anim(fd, 0x03, 0x00FF)
        else:
            self._anim(fd, 0x02, anim_id)  # finish save
            if anim_id == 0x0061:
                self._anim(fd, 0x06, anim_id)  # set default
            self._anim(fd, 0x05, anim_id)  # play

    def _play(self, fd, groups, save=True):
        # 1. Active running animation slot (immediate display)
        self._play_groups(fd, groups, anim_id=0xFFFF)
        if save:
            # 2. Persistent post-boot slot (survives reboots)
            self._play_groups(fd, groups, anim_id=0x0061)
            # 3. Active AC / Battery power animation slots
            for slot in [0x5C, 0x5D, 0x5F]:
                self._play_groups(fd, groups, anim_id=slot)

    def set_static(self, r, g, b, brightness=100, save=True):
        with open(self.dev_path, "r+b", buffering=0) as f:
            fd = f.fileno()
            self._dim(fd, brightness)
            all_zones = list(range(self.zone_count))
            actions = [(0x00, 0x07D0, 0x00FA, r, g, b)]
            self._play(fd, [(all_zones, actions)], save=save)
        if save:
            self.save_state({"effect": "static", "r": r, "g": g, "b": b, "brightness": brightness})

    def set_zones(self, zone_colors, brightness=100, save=True):
        with open(self.dev_path, "r+b", buffering=0) as f:
            fd = f.fileno()
            self._dim(fd, brightness)
            groups = []
            for section, c in zip(self.section_zones, zone_colors):
                groups.append((section, [(0x00, 0x07D0, 0x00FA, c[0], c[1], c[2])]))
            self._play(fd, groups, save=save)
        if save:
            self.save_state({"effect": "zones", "zone_colors": zone_colors, "brightness": brightness})

    def set_pulse(self, r, g, b, speed=5, brightness=100, save=True):
        dur, tempo = self._timing(speed)
        with open(self.dev_path, "r+b", buffering=0) as f:
            fd = f.fileno()
            self._dim(fd, brightness)
            all_zones = list(range(self.zone_count))
            actions = [
                (0x02, dur, tempo, r, g, b),
                (0x02, dur, tempo, 0, 0, 0),
            ]
            self._play(fd, [(all_zones, actions)], save=save)
        if save:
            self.save_state({"effect": "pulse", "r": r, "g": g, "b": b, "speed": speed, "brightness": brightness})

    def set_morph(self, c1, c2, speed=5, brightness=100, save=True):
        dur, tempo = self._timing(speed)
        with open(self.dev_path, "r+b", buffering=0) as f:
            fd = f.fileno()
            self._dim(fd, brightness)
            all_zones = list(range(self.zone_count))
            actions = [
                (0x02, dur, tempo, c1[0], c1[1], c1[2]),
                (0x02, dur, tempo, c2[0], c2[1], c2[2]),
            ]
            self._play(fd, [(all_zones, actions)], save=save)
        if save:
            self.save_state({"effect": "morph", "c1": c1, "c2": c2, "speed": speed, "brightness": brightness})

    def set_cycle(self, colors=None, speed=5, brightness=100, save=True):
        colors = colors or SPECTRUM
        dur, tempo = self._timing(speed)
        actions = [(0x02, dur, tempo, c[0], c[1], c[2]) for c in colors]
        with open(self.dev_path, "r+b", buffering=0) as f:
            fd = f.fileno()
            self._dim(fd, brightness)
            all_zones = list(range(self.zone_count))
            self._play(fd, [(all_zones, actions)], save=save)
        if save:
            self.save_state({"effect": "cycle", "colors": colors, "speed": speed, "brightness": brightness})

    def set_rainbow(self, speed=5, brightness=100, save=True):
        colors = SPECTRUM
        dur, tempo = self._timing(speed)
        groups = []
        for i, section in enumerate(self.section_zones):
            offset = i * len(colors) // len(self.section_zones)
            section_actions = [
                (0x02, dur, tempo, colors[(j + offset) % len(colors)][0],
                 colors[(j + offset) % len(colors)][1],
                 colors[(j + offset) % len(colors)][2])
                for j in range(len(colors))
            ]
            groups.append((section, section_actions))
        with open(self.dev_path, "r+b", buffering=0) as f:
            fd = f.fileno()
            self._dim(fd, brightness)
            self._play(fd, groups, save=save)
        if save:
            self.save_state({"effect": "rainbow", "speed": speed, "brightness": brightness})

    def set_brightness(self, brightness):
        with open(self.dev_path, "r+b", buffering=0) as f:
            self._dim(f.fileno(), brightness)
        state = self.load_state()
        state["brightness"] = brightness
        self.save_state(state)

    def turn_off(self, save=True):
        with open(self.dev_path, "r+b", buffering=0) as f:
            self._dim(f.fileno(), 0)
        if save:
            state = self.load_state()
            state["off"] = True
            self.save_state(state)

    def turn_on(self):
        state = self.load_state()
        state.pop("off", None)
        if state.get("brightness", 100) == 0:
            state["brightness"] = 100
        self.save_state(state)
        self.restore_state()

    def toggle(self):
        state = self.load_state()
        if state.get("off", False) or state.get("brightness", 100) == 0:
            self.turn_on()
            return True
        else:
            self.turn_off()
            return False

    def save_state(self, state):
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
        except OSError:
            pass

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"effect": "static", "r": 0, "g": 136, "b": 255, "brightness": 100}

    def restore_state(self):
        state = self.load_state()
        if state.get("off", False):
            self.turn_off(save=False)
            return
        eff = state.get("effect", "static")
        b = state.get("brightness", 100)
        spd = state.get("speed", 5)
        if eff == "static":
            self.set_static(state.get("r", 0), state.get("g", 136), state.get("b", 255), brightness=b, save=False)
        elif eff == "zones":
            self.set_zones(state.get("zone_colors", [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]), brightness=b, save=False)
        elif eff == "pulse":
            self.set_pulse(state.get("r", 0), state.get("g", 128), state.get("b", 255), speed=spd, brightness=b, save=False)
        elif eff == "morph":
            c1 = tuple(state.get("c1", (255, 0, 0)))
            c2 = tuple(state.get("c2", (0, 0, 255)))
            self.set_morph(c1, c2, speed=spd, brightness=b, save=False)
        elif eff == "cycle":
            cols = [tuple(c) for c in state.get("colors", SPECTRUM)]
            self.set_cycle(colors=cols, speed=spd, brightness=b, save=False)
        elif eff == "rainbow":
            self.set_rainbow(speed=spd, brightness=b, save=False)
