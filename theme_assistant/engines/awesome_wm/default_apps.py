# theme_assistant/engines/awesome_wm/default_apps.py
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any


def _rc_path() -> Path:
    local = Path.home() / ".config" / "awesome" / "rc.lua"
    if local.exists():
        return local
    return Path("/etc/xdg/awesome/rc.lua")


def _read_rc() -> str:
    path = _rc_path()
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _write_rc(content: str) -> None:
    path = Path.home() / ".config" / "awesome" / "rc.lua"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read() -> Dict[str, Any]:
    rc = _read_rc()
    if not rc:
        return {}
    result: Dict[str, Any] = {}
    patterns = {
        "terminal": r'_G\.terminal\s*=\s*"([^"]*)"',
        "browser": r'_G\.browser\s*=\s*"([^"]*)"',
        "editor": r'_G\.editor\s*=\s*[^"=]*"([^"]*)"',  # handles os.getenv fallback
    }
    for key, pat in patterns.items():
        match = re.search(pat, rc)
        if match:
            result[key] = match.group(1)
    return result


def apply(config: Dict[str, Any]) -> None:
    rc = _read_rc()
    if not rc:
        return

    # Update each known key if present in config
    replacements = {
        "terminal": (r'(_G\.terminal\s*=\s*)"[^"]*"', rf'\1"{config["terminal"]}"'),
        "browser": (r'(_G\.browser\s*=\s*)"[^"]*"', rf'\1"{config["browser"]}"'),
        "editor": (r'(_G\.editor\s*=\s*[^"]*)"[^"]*"', rf'\1"{config["editor"]}"'),
    }

    for key, (pattern, repl) in replacements.items():
        if key in config:
            rc = re.sub(pattern, repl, rc)

    _write_rc(rc)