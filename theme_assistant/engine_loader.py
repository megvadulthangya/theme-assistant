# theme_assistant/engine_loader.py
"""Dynamic engine loader and common engine interface."""
from __future__ import annotations

import importlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

import yaml


class BaseEngine(ABC):
    """Abstract base class for all theme engines."""

    @abstractmethod
    def apply(self, config: Dict[str, Any]) -> None:
        """Apply configuration to the target system."""
        ...

    @abstractmethod
    def export(self, config: Dict[str, Any], export_config: Dict[str, Any]) -> None:
        """Write configuration files to disk."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all configuration previously written by this engine."""
        ...


def load_engines(engines_yaml_path: Path) -> Dict[str, BaseEngine]:
    """
    Read the engines YAML manifest, dynamically import each engine module,
    validate its Engine class, and return a dictionary mapping engine ID -> instance.
    """
    if not engines_yaml_path.is_file():
        raise FileNotFoundError(f"Engines manifest not found: {engines_yaml_path}")

    with engines_yaml_path.open("r", encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh)

    engines: Dict[str, BaseEngine] = {}
    for entry in manifest.get("engines", []):
        engine_id = entry["id"]
        module_name = entry["module"]

        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise ImportError(
                f"Failed to import engine module '{module_name}' for id '{engine_id}'"
            ) from exc

        # Every engine module must expose a class named 'Engine' that subclasses BaseEngine.
        engine_class = getattr(module, "Engine", None)
        if engine_class is None:
            raise AttributeError(
                f"Module '{module_name}' does not define a class named 'Engine'"
            )
        if not issubclass(engine_class, BaseEngine):
            raise TypeError(
                f"Engine class in '{module_name}' must be a subclass of BaseEngine"
            )

        engines[engine_id] = engine_class()

    return engines