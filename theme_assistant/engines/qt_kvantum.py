# theme_assistant/engines/qt_kvantum.py
from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Any

from theme_assistant.engine_loader import BaseEngine


class Engine(BaseEngine):
    """Manage Kvantum theme configuration."""

    def __init__(self) -> None:
        self.target = Path.home() / ".config" / "Kvantum" / "kvantum.kvconfig"

    def apply(self, config: Dict[str, Any]) -> None:
        pass

    def export(self, config: Dict[str, Any], export_config: Dict[str, Any]) -> None:
        theme_name = config.get("gtk_theme")
        if theme_name is None:
            return

        self.target.parent.mkdir(parents=True, exist_ok=True)

        parser = ConfigParser()
        if self.target.exists():
            parser.read(self.target, encoding="utf-8")

        if not parser.has_section("General"):
            parser.add_section("General")

        parser.set("General", "theme", str(theme_name))

        with self.target.open("w", encoding="utf-8") as fh:
            parser.write(fh, space_around_delimiters=False)

    def clear(self) -> None:
        if self.target.exists():
            self.target.unlink()