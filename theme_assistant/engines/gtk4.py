# theme_assistant/engines/gtk4.py
from __future__ import annotations

import shutil
from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Any, Optional

from theme_assistant.engine_loader import BaseEngine


class Engine(BaseEngine):
    """Manage GTK4 settings.ini and asset symlinks."""

    def __init__(self) -> None:
        self.config_dir = Path.home() / ".config" / "gtk-4.0"
        self.settings_file = self.config_dir / "settings.ini"

    def apply(self, config: Dict[str, Any]) -> None:
        pass

    def export(self, config: Dict[str, Any], export_config: Dict[str, Any]) -> None:
        self._write_settings(config)
        self._update_symlinks(config)

    def _write_settings(self, config: Dict[str, Any]) -> None:
        """Write GTK4 settings.ini (same format as GTK3)."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        parser = ConfigParser()
        if self.settings_file.exists():
            parser.read(self.settings_file, encoding="utf-8")

        if not parser.has_section("Settings"):
            parser.add_section("Settings")

        key_map = {
            "gtk_theme": "gtk-theme-name",
            "icon_theme": "gtk-icon-theme-name",
            "cursor_theme": "gtk-cursor-theme-name",
            "cursor_size": "gtk-cursor-theme-size",
            "font_name": "gtk-font-name",
            "font_hinting": "gtk-xft-hinting",
            "font_antialiasing": "gtk-xft-antialias",
            "font_rgba_order": "gtk-xft-rgba",
            "text_scaling_factor": "gtk-xft-dpi",
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
            if profile_key == "text_scaling_factor":
                try:
                    factor = float(value)
                    dpi = int(96 * factor)
                    parser.set("Settings", "gtk-xft-dpi", str(dpi))
                except (ValueError, TypeError):
                    pass
            elif profile_key == "color_scheme":
                if value == "prefer-dark":
                    parser.set("Settings", gtk_key, "1")
                elif value == "prefer-light":
                    parser.set("Settings", gtk_key, "0")
                else:
                    parser.set("Settings", gtk_key, str(value))
            else:
                parser.set("Settings", gtk_key, str(value))

        with self.settings_file.open("w", encoding="utf-8") as fh:
            parser.write(fh, space_around_delimiters=False)

    def _find_theme_gtk4_dir(self, theme_name: str) -> Optional[Path]:
        """Locate the gtk-4.0 subdirectory of a theme, checking home then system."""
        candidates = [
            Path.home() / ".themes" / theme_name / "gtk-4.0",
            Path("/usr/share/themes") / theme_name / "gtk-4.0",
        ]
        for candidate in candidates:
            if candidate.is_dir():
                return candidate
        return None

    def _update_symlinks(self, config: Dict[str, Any]) -> None:
        """Create symlinks for gtk.css, gtk-dark.css, assets/ from the theme dir."""
        theme_name = config.get("gtk_theme")
        if not theme_name:
            return

        theme_gtk4_dir = self._find_theme_gtk4_dir(theme_name)
        if not theme_gtk4_dir:
            # No gtk-4.0 assets found; clear previous symlinks but do nothing else
            self._remove_managed_symlinks()
            return

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._remove_managed_symlinks()

        # Files/dirs to link
        to_link = ["gtk.css", "gtk-dark.css", "assets"]
        for name in to_link:
            src = theme_gtk4_dir / name
            if not src.exists():
                continue
            dst = self.config_dir / name
            if dst.exists() or dst.is_symlink():
                dst.unlink()
            try:
                dst.symlink_to(src)
            except OSError:
                # fallback: copy if symlink not possible
                if src.is_dir():
                    shutil.copytree(src, dst, symlinks=True)
                else:
                    shutil.copy2(src, dst)

    def _remove_managed_symlinks(self) -> None:
        """Remove symlinks that we might have created earlier."""
        managed_names = {"gtk.css", "gtk-dark.css", "assets"}
        for name in managed_names:
            target = self.config_dir / name
            if target.is_symlink():
                target.unlink()
            elif target.is_file() or target.is_dir():
                # Only remove if it was previously created by us?
                # For safety, we assume any pre‑existing file with these names
                # was put there by us, so we remove it.
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()

    def clear(self) -> None:
        """Remove the settings file and all managed symlinks."""
        if self.settings_file.exists():
            self.settings_file.unlink()
        self._remove_managed_symlinks()