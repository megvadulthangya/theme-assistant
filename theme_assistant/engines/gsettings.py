# theme_assistant/engines/gsettings.py
from __future__ import annotations

import subprocess
from typing import Dict, Any

from theme_assistant.engine_loader import BaseEngine


class Engine(BaseEngine):
    """Apply theme settings via the gsettings command-line tool."""

    def apply(self, config: Dict[str, Any]) -> None:
        self._set_interface(config)
        self._set_sound(config)

    def export(self, config: Dict[str, Any], export_config: Dict[str, Any]) -> None:
        pass

    def clear(self) -> None:
        """Nothing to clear; gsettings is a runtime-only operation."""
        pass

    def _set_interface(self, config: Dict[str, Any]) -> None:
        schema = "org.gnome.desktop.interface"
        key_map = {
            "gtk_theme": "gtk-theme",
            "icon_theme": "icon-theme",
            "cursor_theme": "cursor-theme",
            "cursor_size": "cursor-size",
            "font_name": "font-name",
            "toolbar_style": "toolbar-style",
            "font_hinting": "font-hinting",
            "font_antialiasing": "font-antialiasing",
            "font_rgba_order": "font-rgba-order",
            "text_scaling_factor": "text-scaling-factor",
            "color_scheme": "color-scheme",
        }

        for profile_key, gkey in key_map.items():
            value = config.get(profile_key)
            if value is None:
                continue
            self._set(schema, gkey, value)

    def _set_sound(self, config: Dict[str, Any]) -> None:
        schema = "org.gnome.desktop.sound"
        key_map = {
            "event_sounds": "event-sounds",
            "input_feedback_sounds": "input-feedback-sounds",
        }
        for profile_key, gkey in key_map.items():
            value = config.get(profile_key)
            if value is None:
                continue
            self._set(schema, gkey, value)

    @staticmethod
    def _set(schema: str, key: str, value: Any) -> None:
        if isinstance(value, bool):
            value = "true" if value else "false"
        elif isinstance(value, int):
            value = str(value)
        elif isinstance(value, float):
            value = str(value)
        else:
            # GVariant requires string values to be explicitly quoted
            value = f"'{value}'"
        subprocess.run(
            ["gsettings", "set", schema, key, value],
            check=False,
            capture_output=True,
        )