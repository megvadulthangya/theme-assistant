# theme_assistant/engines/cursor_fallback.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, Optional

from theme_assistant.engine_loader import BaseEngine


class Engine(BaseEngine):
    """Create an index.theme inheritance file for cursor theme fallback."""

    def __init__(self) -> None:
        self._target_path: Optional[Path] = None

    def apply(self, config: Dict[str, Any]) -> None:
        pass

    def export(self, config: Dict[str, Any], export_config: Dict[str, Any]) -> None:
        cursor_theme = config.get("cursor_theme")
        if cursor_theme is None or cursor_theme == "default":
            return

        target = self._get_target_path(create_parent=True)
        self._target_path = target

        content = (
            "[Icon Theme]\n"
            f"Inherits={cursor_theme}\n"
        )
        target.write_text(content, encoding="utf-8")

    def clear(self) -> None:
        target = self._get_target_path(create_parent=False)
        if target.exists():
            target.unlink()
        # If we tracked a previous explicit path, remove it too
        if self._target_path and self._target_path.exists():
            self._target_path.unlink()
            self._target_path = None

    @staticmethod
    def _get_target_path(create_parent: bool = True) -> Path:
        """Resolve the target directory following the specified fallback rules."""
        home_icons = Path.home() / ".icons"
        if home_icons.is_dir():
            default_dir = home_icons / "default"
        else:
            data_home = os.environ.get("XDG_DATA_HOME")
            if data_home:
                default_dir = Path(data_home) / "icons" / "default"
            else:
                default_dir = Path.home() / ".local" / "share" / "icons" / "default"

        if create_parent:
            default_dir.mkdir(parents=True, exist_ok=True)

        return default_dir / "index.theme"