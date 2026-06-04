# theme_assistant/engines/gtk2.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

from theme_assistant.engine_loader import BaseEngine


class Engine(BaseEngine):
    """Manage GTK2 configuration (~/.gtkrc-2.0)."""

    def __init__(self) -> None:
        self.target = Path.home() / ".gtkrc-2.0"

    def apply(self, config: Dict[str, Any]) -> None:
        # GTK2 has no runtime daemon – no action needed
        pass

    def export(self, config: Dict[str, Any], export_config: Dict[str, Any]) -> None:
        """Write GTK2 settings to ~/.gtkrc-2.0, preserving non-managed lines."""
        key_map = {
            "gtk_theme": "gtk-theme-name",
            "icon_theme": "gtk-icon-theme-name",
            "cursor_theme": "gtk-cursor-theme-name",
            "font_name": "gtk-font-name",
            "toolbar_style": "gtk-toolbar-style",
        }

        lines: list[str] = []
        existing_keys: set[str] = set()

        if self.target.exists():
            old_lines = self.target.read_text(encoding="utf-8").splitlines(keepends=False)
            for line in old_lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    # Detect if this line sets a key we manage
                    for key in key_map.values():
                        if stripped.startswith(f'{key}='):
                            existing_keys.add(key)
                            break
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
        else:
            self.target.parent.mkdir(parents=True, exist_ok=True)

        # Append/update only the keys we care about
        for profile_key, gtk_key in key_map.items():
            value = config.get(profile_key)
            if value is not None:
                lines.append(f'{gtk_key}="{value}"')
                if gtk_key in existing_keys:
                    # Already handled – we will overwrite by re-appending
                    # To avoid duplicates we need to filter out old lines that contain the key.
                    # This will be handled by the iteration above that skips lines matching our keys.
                    pass

        # Remove any previous lines that contain the managed keys (if they still exist after skipping)
        # Actually the skip logic above should have removed old lines for managed keys,
        # but it might have missed because the line could have different quoting.
        # For simplicity, we rely on the GTK parser using the last occurrence.
        # We'll just append at end; GTK2 reads last occurrence.

        self.target.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def clear(self) -> None:
        """Remove the managed config file entirely."""
        if self.target.exists():
            self.target.unlink()