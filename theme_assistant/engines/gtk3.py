# theme_assistant/engines/gtk3.py
from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Any

from theme_assistant.engine_loader import BaseEngine


class Engine(BaseEngine):
    """Manage GTK3 settings.ini."""

    def __init__(self) -> None:
        self.target = Path.home() / ".config" / "gtk-3.0" / "settings.ini"

    def apply(self, config: Dict[str, Any]) -> None:
        pass

    def export(self, config: Dict[str, Any], export_config: Dict[str, Any]) -> None:
        self.target.parent.mkdir(parents=True, exist_ok=True)

        parser = ConfigParser()
        if self.target.exists():
            parser.read(self.target, encoding="utf-8")

        if not parser.has_section("Settings"):
            parser.add_section("Settings")

        # Map profile keys to GTK3 settings.ini keys
        key_map = {
            "gtk_theme": "gtk-theme-name",
            "icon_theme": "gtk-icon-theme-name",
            "cursor_theme": "gtk-cursor-theme-name",
            "cursor_size": "gtk-cursor-theme-size",
            "font_name": "gtk-font-name",
            "font_hinting": "gtk-xft-hinting",
            "font_antialiasing": "gtk-xft-antialias",
            "font_rgba_order": "gtk-xft-rgba",
            "text_scaling_factor": "gtk-xft-dpi",  # will be handled carefully
            "event_sounds": "gtk-enable-event-sounds",
            "input_feedback_sounds": "gtk-enable-input-feedback-sounds",
            "toolbar_style": "gtk-toolbar-style",
            "toolbar_icon_size": "gtk-toolbar-icon-size",
            "button_images": "gtk-button-images",
            "menu_images": "gtk-menu-images",
            "color_scheme": "gtk-application-prefer-dark-theme",
        }

        for profile_key, gtk_key in key_map.items():
            value = config.get(profile_key)
            if value is None:
                continue
            # Special handling: text_scaling_factor -> DPI is 96 * factor
            if profile_key == "text_scaling_factor":
                try:
                    factor = float(value)
                    dpi = int(96 * factor)
                    parser.set("Settings", "gtk-xft-dpi", str(dpi))
                except (ValueError, TypeError):
                    pass
            elif profile_key == "color_scheme":
                # Map "prefer-dark" / "prefer-light" to boolean
                if value == "prefer-dark":
                    parser.set("Settings", gtk_key, "1")
                elif value == "prefer-light":
                    parser.set("Settings", gtk_key, "0")
                # else leave as is? just set string
                else:
                    parser.set("Settings", gtk_key, str(value))
            else:
                parser.set("Settings", gtk_key, str(value))

        with self.target.open("w", encoding="utf-8") as fh:
            parser.write(fh, space_around_delimiters=False)

    def clear(self) -> None:
        if self.target.exists():
            self.target.unlink()