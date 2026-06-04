# theme_assistant/engine_loader.py
"""Dynamic engine loader and common engine interface."""
from __future__ import annotations

import importlib
import sys
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
    Gracefully skips placeholder modules that do not define an Engine class.
    """
    if not engines_yaml_path.is_file():
        raise FileNotFoundError(f"Engines manifest not found: {engines_yaml_path}")

    with engines_yaml_path.open("r", encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh)

    engines: Dict[str, BaseEngine] = {}
    for entry in manifest.get("engines", []):
        engine_id = entry["id"]
        module_name = entry["module"]

        # Ensure fully-qualified import path under theme_assistant package
        if not module_name.startswith("theme_assistant."):
            module_name = "theme_assistant." + module_name

        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            print(
                f"Warning: Failed to import engine module '{module_name}' for id '{engine_id}'. Skipping.",
                file=sys.stderr,
            )
            continue

        # Every engine module must expose a class named 'Engine' that subclasses BaseEngine.
        engine_class = getattr(module, "Engine", None)
        if engine_class is None:
            print(
                f"Warning: Module '{module_name}' does not define a class named 'Engine'. Skipping.",
                file=sys.stderr,
            )
            continue
        if not issubclass(engine_class, BaseEngine):
            print(
                f"Warning: Engine class in '{module_name}' is not a subclass of BaseEngine. Skipping.",
                file=sys.stderr,
            )
            continue

        engines[engine_id] = engine_class()

    return engines