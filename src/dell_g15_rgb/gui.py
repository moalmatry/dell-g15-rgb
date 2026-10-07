#!/usr/bin/env python3
"""Dell G15 5515 Keyboard RGB Control Panel (GTK3 GUI)."""
import os
import sys

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from dell_g15_rgb.controller import DellG15RGB, SPECTRUM

PRESET_COLORS = [
    ("#FF0033", "Neon Red"),
    ("#FF6600", "Solar Orange"),
    ("#FFCC00", "Warm Amber"),
    ("#00FF66", "Emerald"),
    ("#00FFFF", "Cyan"),
    ("#0088FF", "Deep Sky"),
    ("#6600FF", "Electric Indigo"),
    ("#CC00FF", "Neon Purple"),
    ("#FFFFFF", "Pure White"),
]


class DellG15RGBApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Dell G15 Keyboard RGB")
        self.set_default_size(520, 580)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("preferences-desktop-keyboard")

        try:
            self.rgb = DellG15RGB()
        except Exception as e:
            self.show_error_dialog(str(e))
            sys.exit(1)

        self.state = self.rgb.load_state()

        # Main Layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        main_box.set_border_width(18)
        self.add(main_box)

        # Header Bar / Switch
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        title_label = Gtk.Label()
        title_label.set_markup("<span size='x-large' weight='bold'>AlienFX Keyboard RGB</span>")
        header_box.pack_start(title_label, False, False, 0)

        self.power_switch = Gtk.Switch()
        self.power_switch.set_active(not self.state.get("off", False))
        self.power_switch.connect("notify::active", self.on_power_toggle)
        header_box.pack_end(self.power_switch, False, False, 0)
        main_box.pack_start(header_box, False, False, 0)

        # Brightness Section
        bright_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        bright_label = Gtk.Label(label="Brightness")
        bright_label.set_halign(Gtk.Align.START)
        bright_box.pack_start(bright_label, False, False, 0)

        self.bright_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 5)
        self.bright_scale.set_value(self.state.get("brightness", 100))
        self.bright_scale.connect("value-changed", self.on_brightness_change)
        bright_box.pack_start(self.bright_scale, False, False, 0)
        main_box.pack_start(bright_box, False, False, 0)

        # Notebook (Tabs)
        notebook = Gtk.Notebook()
        main_box.pack_start(notebook, True, True, 0)

        # Tab 1: Dynamic Effects & Quick Colors
        tab1_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        tab1_box.set_border_width(12)

        # Effects Buttons Grid
        effects_label = Gtk.Label()
        effects_label.set_markup("<b>Dynamic Lighting Effects</b>")
        effects_label.set_halign(Gtk.Align.START)
        tab1_box.pack_start(effects_label, False, False, 0)

        eff_grid = Gtk.Grid()
        eff_grid.set_column_spacing(10)
        eff_grid.set_row_spacing(10)
        eff_grid.set_column_homogeneous(True)

        btn_rainbow = Gtk.Button(label="🌈 Rainbow Wave")
        btn_rainbow.connect("clicked", lambda w: self.apply_rainbow())
        eff_grid.attach(btn_rainbow, 0, 0, 1, 1)

        btn_cycle = Gtk.Button(label="🔄 Spectrum Cycle")
        btn_cycle.connect("clicked", lambda w: self.apply_cycle())
        eff_grid.attach(btn_cycle, 1, 0, 1, 1)

        btn_pulse = Gtk.Button(label="💓 Pulse / Breathe")
        btn_pulse.connect("clicked", lambda w: self.apply_pulse())
        eff_grid.attach(btn_pulse, 0, 1, 1, 1)

        btn_morph = Gtk.Button(label="🎨 2-Color Morph")
        btn_morph.connect("clicked", lambda w: self.apply_morph())
        eff_grid.attach(btn_morph, 1, 1, 1, 1)

        tab1_box.pack_start(eff_grid, False, False, 0)

        # Speed Scale
        speed_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        speed_label = Gtk.Label(label="Animation Speed")
        speed_label.set_halign(Gtk.Align.START)
        speed_box.pack_start(speed_label, False, False, 0)
        self.speed_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 10, 1)
        self.speed_scale.set_value(self.state.get("speed", 5))
        self.speed_scale.connect("value-changed", self.on_speed_change)
        speed_box.pack_start(self.speed_scale, False, False, 0)
        tab1_box.pack_start(speed_box, False, False, 0)

        # Quick Static Colors
        static_label = Gtk.Label()
        static_label.set_markup("<b>Solid Color Presets</b>")
        static_label.set_halign(Gtk.Align.START)
        tab1_box.pack_start(static_label, False, False, 0)

        palette_box = Gtk.FlowBox()
        palette_box.set_max_children_per_line(5)
        palette_box.set_selection_mode(Gtk.SelectionMode.NONE)
        palette_box.set_column_spacing(8)
        palette_box.set_row_spacing(8)

        for hex_code, name in PRESET_COLORS:
            btn = Gtk.Button()
            btn.set_tooltip_text(name)
            # Use colored chip
            da = Gtk.DrawingArea()
            da.set_size_request(32, 24)
            r = int(hex_code[1:3], 16) / 255.0
            g = int(hex_code[3:5], 16) / 255.0
            b = int(hex_code[5:7], 16) / 255.0

            def draw_rect(widget, cr, cr_r=r, cr_g=g, cr_b=b):
                cr.set_source_rgb(cr_r, cr_g, cr_b)
                cr.rectangle(0, 0, 32, 24)
                cr.fill()
            da.connect("draw", draw_rect)
            btn.add(da)
            btn.connect("clicked", lambda w, hc=hex_code: self.apply_static_hex(hc))
            palette_box.add(btn)

        # Custom Color Button
        custom_btn = Gtk.Button(label="Pick Custom...")
        custom_btn.connect("clicked", self.pick_custom_static)
        palette_box.add(custom_btn)

        tab1_box.pack_start(palette_box, False, False, 0)
        notebook.append_page(tab1_box, Gtk.Label(label="Effects & Colors"))

        # Tab 2: 4-Zone Keyboard Customization
        tab2_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        tab2_box.set_border_width(12)

        zone_desc = Gtk.Label()
        zone_desc.set_markup("Customize the <b>4 individual RGB zones</b> across the keyboard:")
        zone_desc.set_halign(Gtk.Align.START)
        tab2_box.pack_start(zone_desc, False, False, 0)

        # 4 Zone buttons
        zones_grid = Gtk.Grid()
        zones_grid.set_column_spacing(10)
        zones_grid.set_column_homogeneous(True)

        self.zone_buttons = []
        default_zone_colors = [
            (255, 0, 0),      # Zone 1
            (0, 255, 0),      # Zone 2
            (0, 128, 255),    # Zone 3
            (255, 0, 255),    # Zone 4
        ]
        saved_zones = self.state.get("zone_colors", default_zone_colors)

        for i in range(4):
            z_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            z_title = Gtk.Label(label=f"Zone {i+1}")
            if i == 0:
                z_sub = Gtk.Label(label="Left")
            elif i == 1:
                z_sub = Gtk.Label(label="Mid-Left")
            elif i == 2:
                z_sub = Gtk.Label(label="Mid-Right")
            else:
                z_sub = Gtk.Label(label="Right")
            z_sub.set_sensitive(False)

            color_btn = Gtk.ColorButton()
            c = saved_zones[i] if i < len(saved_zones) else (255, 255, 255)
            color_btn.set_rgba(Gdk.RGBA(c[0]/255.0, c[1]/255.0, c[2]/255.0, 1.0))
            self.zone_buttons.append(color_btn)

            z_box.pack_start(z_title, False, False, 0)
            z_box.pack_start(z_sub, False, False, 0)
            z_box.pack_start(color_btn, False, False, 0)
            zones_grid.attach(z_box, i, 0, 1, 1)

        tab2_box.pack_start(zones_grid, False, False, 10)

        apply_zones_btn = Gtk.Button(label="Apply 4-Zone Lighting")
        apply_zones_btn.connect("clicked", self.apply_zones)
        tab2_box.pack_start(apply_zones_btn, False, False, 0)

        notebook.append_page(tab2_box, Gtk.Label(label="4-Zone Custom"))

        # Status Bar / Message
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.set_sensitive(False)
        main_box.pack_end(self.status_label, False, False, 0)

    def set_status(self, msg):
        self.status_label.set_text(msg)

    def on_power_toggle(self, switch, gparam):
        if switch.get_active():
            self.rgb.turn_on()
            self.set_status("Keyboard backlighting enabled")
        else:
            self.rgb.turn_off()
            self.set_status("Keyboard backlighting disabled")

    def on_brightness_change(self, scale):
        b = int(scale.get_value())
        self.rgb.set_brightness(b)
        self.set_status(f"Brightness: {b}%")

    def on_speed_change(self, scale):
        spd = int(scale.get_value())
        self.state["speed"] = spd
        self.rgb.save_state(self.state)

    def apply_rainbow(self):
        spd = int(self.speed_scale.get_value())
        b = int(self.bright_scale.get_value())
        self.rgb.set_rainbow(speed=spd, brightness=b)
        self.set_status(f"Applied Rainbow Wave (Speed {spd})")

    def apply_cycle(self):
        spd = int(self.speed_scale.get_value())
        b = int(self.bright_scale.get_value())
        self.rgb.set_cycle(speed=spd, brightness=b)
        self.set_status(f"Applied Spectrum Cycle (Speed {spd})")

    def apply_pulse(self):
        # Pick color dialog for pulse
        dialog = Gtk.ColorChooserDialog(title="Choose Pulse Color", transient_for=self)
        if dialog.run() == Gtk.ResponseType.OK:
            rgba = dialog.get_rgba()
            r, g, b = int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255)
            spd = int(self.speed_scale.get_value())
            br = int(self.bright_scale.get_value())
            self.rgb.set_pulse(r, g, b, speed=spd, brightness=br)
            self.set_status(f"Applied Pulse #{r:02x}{g:02x}{b:02x}")
        dialog.destroy()

    def apply_morph(self):
        # Morph dialog
        dialog1 = Gtk.ColorChooserDialog(title="Choose 1st Morph Color", transient_for=self)
        if dialog1.run() == Gtk.ResponseType.OK:
            rgba1 = dialog1.get_rgba()
            c1 = (int(rgba1.red * 255), int(rgba1.green * 255), int(rgba1.blue * 255))
            dialog1.destroy()
            dialog2 = Gtk.ColorChooserDialog(title="Choose 2nd Morph Color", transient_for=self)
            if dialog2.run() == Gtk.ResponseType.OK:
                rgba2 = dialog2.get_rgba()
                c2 = (int(rgba2.red * 255), int(rgba2.green * 255), int(rgba2.blue * 255))
                spd = int(self.speed_scale.get_value())
                br = int(self.bright_scale.get_value())
                self.rgb.set_morph(c1, c2, speed=spd, brightness=br)
                self.set_status("Applied 2-Color Morph")
            dialog2.destroy()
        else:
            dialog1.destroy()

    def apply_static_hex(self, hex_code):
        r = int(hex_code[1:3], 16)
        g = int(hex_code[3:5], 16)
        b = int(hex_code[5:7], 16)
        br = int(self.bright_scale.get_value())
        self.rgb.set_static(r, g, b, brightness=br)
        self.set_status(f"Applied solid {hex_code}")

    def pick_custom_static(self, widget):
        dialog = Gtk.ColorChooserDialog(title="Choose Custom Color", transient_for=self)
        if dialog.run() == Gtk.ResponseType.OK:
            rgba = dialog.get_rgba()
            r, g, b = int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255)
            br = int(self.bright_scale.get_value())
            self.rgb.set_static(r, g, b, brightness=br)
            self.set_status(f"Applied #{r:02x}{g:02x}{b:02x}")
        dialog.destroy()

    def apply_zones(self, widget):
        colors = []
        for btn in self.zone_buttons:
            rgba = btn.get_rgba()
            colors.append((int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255)))
        br = int(self.bright_scale.get_value())
        self.rgb.set_zones(colors, brightness=br)
        self.set_status("Applied custom 4-zone colors")

    def show_error_dialog(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="RGB Controller Error",
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()


def main():
    app = DellG15RGBApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
