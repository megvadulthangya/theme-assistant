from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any

from theme_assistant.engine_loader import BaseEngine


class Engine(BaseEngine):
    """Manage cursor theme, size, and fallback index.theme generation."""

    def __init__(self) -> None:
        self._xresources = Path.home() / ".Xresources"
        self._fallback_dir: Path | None = None
        self._fallback_file: Path | None = None

    def apply(self, config: Dict[str, Any]) -> None:
        # Runtime cursor changes are handled by other tools (e.g., xsetroot)
        pass

    def export(self, config: Dict[str, Any], export_config: Dict[str, Any]) -> None:
        cursor_theme = config.get("cursor_theme")
        cursor_size = config.get("cursor_size")

        # 1. Update ~/.Xresources
        self._write_xresources(cursor_theme, cursor_size)

        # 2. Write fallback index.theme if appropriate
        if cursor_theme and cursor_theme != "default":
            self._write_fallback_index(cursor_theme)
        else:
            self._remove_fallback_index()

    def clear(self) -> None:
        # Remove managed lines from Xresources
        if self._xresources.exists():
            lines = self._xresources.read_text(encoding="utf-8").splitlines(keepends=True)
            filtered = [
                line for line in lines
                if not line.lstrip().startswith("Xcursor.theme:") and not line.lstrip().startswith("Xcursor.size:")
            ]
            if filtered:
                self._xresources.write_text("".join(filtered), encoding="utf-8")
            else:
                self._xresources.unlink()

        self._remove_fallback_index()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _write_xresources(self, theme: str | None, size: Any | None) -> None:
        if not theme and size is None:
            return

        lines: list[str] = []
        managed_keys = {"Xcursor.theme", "Xcursor.size"}

        if self._xresources.exists():
            for line in self._xresources.read_text(encoding="utf-8").splitlines(keepends=True):
                stripped = line.lstrip()
                if any(stripped.startswith(key) for key in managed_keys):
                    continue  # will be replaced
                lines.append(line)
        else:
            self._xresources.parent.mkdir(parents=True, exist_ok=True)

        if theme:
            lines.append(f"Xcursor.theme: {theme}\n")
        if size is not None:
            try:
                size_int = int(size)
                lines.append(f"Xcursor.size: {size_int}\n")
            except (ValueError, TypeError):
                pass

        self._xresources.write_text("".join(lines), encoding="utf-8")

    def _get_fallback_path(self) -> Path | None:
        """Return the path to index.theme inside the icons/default directory, or None if not applicable."""
        candidates = [
            Path.home() / ".icons" / "default",
        ]
        data_home = os.environ.get("XDG_DATA_HOME")
        if data_home:
            candidates.append(Path(data_home) / "icons" / "default")
        candidates.append(Path.home() / ".local" / "share" / "icons" / "default")

        for directory in candidates:
            if directory.is_dir() or directory.parent.is_dir():
                return directory / "index.theme"
        return None

    def _write_fallback_index(self, cursor_theme: str) -> None:
        path = self._get_fallback_path()
        if not path:
            # Try the first candidate anyway, creating it
            path = Path.home() / ".icons" / "default" / "index.theme"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"[Icon Theme]\nInherits={cursor_theme}\n",
            encoding="utf-8",
        )
        self._fallback_file = path

    def _remove_fallback_index(self) -> None:
        if self._fallback_file and self._fallback_file.exists():
            self._fallback_file.unlink()
            self._fallback_file = None
        # Also try to remove any leftover fallback from the first candidate
        default_path = Path.home() / ".icons" / "default" / "index.theme"
        if default_path.exists():
            default_path.unlink()