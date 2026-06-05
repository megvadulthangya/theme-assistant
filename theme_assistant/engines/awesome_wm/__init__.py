# theme_assistant/engines/awesome_wm/__init__.py
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, Any

from theme_assistant.engine_loader import BaseEngine
from theme_assistant.engines.awesome_wm import appearance
from theme_assistant.engines.awesome_wm import default_apps


class Engine(BaseEngine):
    """Orchestrates AwesomeWM configuration via submodules."""

    def __init__(self) -> None:
        self._config_dir = Path.home() / ".config" / "awesome"
        self._system_skeleton = Path("/etc/xdg/awesome")

    def apply(self, config: Dict[str, Any]) -> None:
        self._ensure_config_exists()
        appearance.apply(config)
        default_apps.apply(config)

    def export(self, config: Dict[str, Any], export_config: Dict[str, Any]) -> None:
        pass

    def clear(self) -> None:
        if self._config_dir.exists():
            shutil.rmtree(self._config_dir)

    def read(self) -> Dict[str, Any]:
        state: Dict[str, Any] = {}
        state.update(appearance.read())
        state.update(default_apps.read())
        return state

    def _ensure_config_exists(self) -> None:
        if not self._config_dir.exists():
            if self._system_skeleton.exists():
                shutil.copytree(self._system_skeleton, self._config_dir, symlinks=True)
            else:
                self._config_dir.mkdir(parents=True, exist_ok=True)