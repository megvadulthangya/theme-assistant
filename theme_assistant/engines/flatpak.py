# theme_assistant/engines/flatpak.py
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any

from theme_assistant.engine_loader import BaseEngine


class Engine(BaseEngine):
    """Manage Flatpak overrides for themes and icons."""

    def apply(self, config: Dict[str, Any]) -> None:
        if shutil.which("flatpak") is None:
            return

        gtk_theme = config.get("gtk_theme")
        icon_theme = config.get("icon_theme")

        if gtk_theme:
            self._run_flatpak("override", "--user", f"--env=GTK_THEME={gtk_theme}")

        if icon_theme:
            self._run_flatpak("override", "--user", f"--env=ICON_THEME={icon_theme}")

        # Always allow access to user themes directory – resolve $HOME dynamically
        themes_path = Path.home() / ".themes"
        self._run_flatpak("override", "--user", f"--filesystem={themes_path}:ro")

    def export(self, config: Dict[str, Any], export_config: Dict[str, Any]) -> None:
        pass

    def clear(self) -> None:
        if shutil.which("flatpak") is None:
            return

        self._run_flatpak("override", "--user", "--unset-env=GTK_THEME")
        self._run_flatpak("override", "--user", "--unset-env=ICON_THEME")

    @staticmethod
    def _run_flatpak(*args: str) -> None:
        subprocess.run(
            ["flatpak", *args],
            check=False,
            capture_output=True,
        )