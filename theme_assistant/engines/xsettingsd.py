# theme_assistant/engines/xsettingsd.py
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any

from theme_assistant.engine_loader import BaseEngine


class Engine(BaseEngine):
    """Manage ~/.xsettingsd configuration."""

    def __init__(self) -> None:
        self.target = Path.home() / ".xsettingsd"

    def apply(self, config: Dict[str, Any]) -> None:
        pass

    def export(self, config: Dict[str, Any], export_config: Dict[str, Any]) -> None:
        key_map = {
            "gtk_theme": "Net/ThemeName",
            "icon_theme": "Net/IconThemeName",
            "cursor_theme": "Gtk/CursorThemeName",
            "cursor_size": "Gtk/CursorThemeSize",
            "font_name": "Gtk/FontName",
        }

        managed_x_keys = set(key_map.values())
        output_lines: list[str] = []
        seen_managed: set[str] = set()

        if self.target.exists():
            with self.target.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.rstrip("\n")
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        output_lines.append(line)
                        continue
                    # Attempt to parse key / value
                    match = re.match(r'^\s*([A-Za-z0-9_/]+)\s+(.*)', line)
                    if match:
                        key = match.group(1)
                        if key in managed_x_keys:
                            seen_managed.add(key)
                            continue  # will be replaced
                    output_lines.append(line)
        else:
            self.target.parent.mkdir(parents=True, exist_ok=True)

        # Append our managed keys
        for profile_key, xkey in key_map.items():
            value = config.get(profile_key)
            if value is None:
                continue
            if profile_key == "cursor_size":
                try:
                    int_val = int(value)
                    output_lines.append(f"{xkey} {int_val}")
                except (ValueError, TypeError):
                    pass
            else:
                output_lines.append(f'{xkey} "{value}"')

        self.target.write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    def clear(self) -> None:
        if self.target.exists():
            self.target.unlink()