# theme_assistant/engines/awesome_wm/appearance.py
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any, List, Optional

RC_CONTENT = str  # type alias for readability


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


def _parse_themes(rc: str) -> List[str]:
    """Extract the theme list from rc.lua (themes = { ... })."""
    # Match the whole table definition
    match = re.search(r"local\s+themes\s*=\s*\{(.*?)\}", rc, re.DOTALL)
    if not match:
        return []
    table_body = match.group(1)
    # Extract quoted theme names
    themes = re.findall(r'"([^"]+)"', table_body)
    return themes


def read() -> Dict[str, Any]:
    rc = _read_rc()
    if not rc:
        return {}
    # Extract chosen_theme index: local chosen_theme = themes[7]
    match = re.search(r"local\s+chosen_theme\s*=\s*themes\[(\d+)\]", rc)
    if not match:
        return {}
    index = int(match.group(1))
    themes = _parse_themes(rc)
    if 1 <= index <= len(themes):
        return {"awesome_theme": themes[index - 1]}
    return {}


def apply(config: Dict[str, Any]) -> None:
    rc = _read_rc()
    if not rc:
        return

    theme_name = config.get("awesome_theme")
    if not theme_name:
        return

    themes = _parse_themes(rc)
    if not themes:
        return

    # Find index for the given theme name (case-insensitive)
    try:
        idx = themes.index(theme_name)
    except ValueError:
        # Maybe case-insensitive
        lower_name = theme_name.lower()
        matches = [i for i, t in enumerate(themes) if t.lower() == lower_name]
        if not matches:
            return
        idx = matches[0]
    new_index = idx + 1  # Lua arrays are 1-indexed

    # Replace the chosen_theme line
    pattern = r"(local\s+chosen_theme\s*=\s*themes\[)\d+(\])"
    replacement = rf"\g<1>{new_index}\g<2>"
    new_rc = re.sub(pattern, replacement, rc)

    _write_rc(new_rc)