# theme_assistant/core.py
"""Core orchestrator: loads a profile, distributes config to engines, handles export toggles."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import yaml

from theme_assistant.engine_loader import load_engines

# Mapping from engine ID to the export toggle key found in the profile's 'export' section.
_EXPORT_TOGGLE_MAP: Dict[str, str] = {
    "gtk2": "gtkrc_2_0",
    "gtk3": "settings_ini",
    "gtk4": "gtk4_symlinks",
    "icons": "index_theme",
    "xsettingsd": "xsettingsd",
    "flatpak": "flatpak_overrides",
}


def run(profile_path: Path, engines_yaml_path: Path) -> None:
    """
    Load the profile and the engine set, then apply and (optionally) export
    the configuration for each engine according to the export toggles.
    """
    if not profile_path.is_file():
        raise FileNotFoundError(f"Profile file not found: {profile_path}")

    engines = load_engines(engines_yaml_path)

    with profile_path.open("r", encoding="utf-8") as fh:
        profile_data = yaml.safe_load(fh)

    gtk_config = profile_data.get("gtk", {})
    awesome_config = profile_data.get("awesome_wm", {})
    export_config = profile_data.get("export", {})

    for engine_id, engine in engines.items():
        # Distribute the appropriate configuration section
        if engine_id == "awesome_wm":
            config = awesome_config
        else:
            config = gtk_config

        # Apply always runs
        engine.apply(config)

        # Determine whether export should be called
        if engine_id in _EXPORT_TOGGLE_MAP:
            toggle_key = _EXPORT_TOGGLE_MAP[engine_id]
            if export_config.get(toggle_key, False):
                engine.export(config, export_config)
        else:
            # Engines without a dedicated toggle (fonts, cursors, placeholders, awesome_wm, etc.)
            # export unconditionally.
            engine.export(config, export_config)