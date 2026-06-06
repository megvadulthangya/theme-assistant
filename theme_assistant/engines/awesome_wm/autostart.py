# theme_assistant/engines/awesome_wm/autostart.py
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


def _autostart_path() -> Path:
    local = Path.home() / ".config" / "awesome" / "configuration" / "autostart.lua"
    if local.exists():
        return local
    fallback = Path("/etc/xdg/awesome/configuration/autostart.lua")
    if fallback.exists():
        return fallback
    return local  # return user path even if missing, for writing


def _read_autostart() -> str:
    path = _autostart_path()
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _write_autostart(content: str) -> None:
    path = Path.home() / ".config" / "awesome" / "configuration" / "autostart.lua"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read() -> Dict[str, Any]:
    rc = _read_autostart()
    if not rc:
        return {}

    # Locate run_once({ ... }) block
    match = re.search(r"run_once\s*\(\s*\{(.*?)\}\s*\)", rc, re.DOTALL)
    if not match:
        return {}

    block = match.group(1)
    active_commands: List[str] = []

    # Parse each line in the block
    for line in block.split("\n"):
        # Look for lines that contain a quoted string (potential command)
        cmd_match = re.search(r'"([^"]*)"', line)
        if not cmd_match:
            continue
        cmd = cmd_match.group(1)
        # Check if the line is active (not commented out)
        # Active lines start with optional whitespace then a quote, not with --
        stripped = line.lstrip()
        if not stripped.startswith("--"):
            active_commands.append(cmd)

    return {"autostart": active_commands}


def apply(config: Dict[str, Any]) -> None:
    autostart_cmds = config.get("autostart")
    if not autostart_cmds or not isinstance(autostart_cmds, list):
        return

    desired_set = set(autostart_cmds)
    rc = _read_autostart()

    # If the file does not exist or has no run_once block, create a minimal one
    if not rc or "run_once" not in rc:
        _create_minimal_autostart(desired_set)
        return

    # Locate the block boundaries
    block_match = re.search(
        r"(run_once\s*\(\s*\{)(.*?)(\}\s*\))", rc, re.DOTALL
    )
    if not block_match:
        # No block found, recreate the file
        _create_minimal_autostart(desired_set)
        return

    before_block = rc[: block_match.start()]
    after_block = rc[block_match.end() :]
    block_prefix = block_match.group(1)  # "run_once({"
    block_suffix = block_match.group(3)  # "})"
    block_body = block_match.group(2)

    lines = block_body.split("\n")
    new_lines: List[str] = []
    seen_commands: set = set()

    # Determine indentation from existing active command lines, or fallback
    default_indent = _guess_indent(lines)

    for line in lines:
        parsed = _parse_command_line(line)
        if parsed is None:
            # Not a command line – keep as is
            new_lines.append(line)
            continue

        cmd = parsed["command"]
        seen_commands.add(cmd)

        if cmd in desired_set:
            # Ensure enabled
            if not parsed["enabled"]:
                # Enable: rebuild the line without the comment marker
                enabled_line = _enable_line(parsed)
                new_lines.append(enabled_line)
            else:
                new_lines.append(line)  # already enabled
        else:
            # Command not wanted -> disable if active
            if parsed["enabled"]:
                disabled_line = f"--{line}"  # prepend comment
                new_lines.append(disabled_line)
            else:
                new_lines.append(line)  # already disabled

    # Append missing commands from config
    missing = desired_set - seen_commands
    for cmd in autostart_cmds:  # preserve order from config
        if cmd in missing:
            new_line = f'{default_indent}"{cmd}",'
            new_lines.append(new_line)

    # Reassemble the block
    new_block_body = "\n".join(new_lines)
    # Ensure proper newline before closing bracket if not empty
    if new_block_body and not new_block_body.endswith("\n"):
        new_block_body += "\n"
    new_rc = before_block + block_prefix + new_block_body + block_suffix + after_block
    _write_autostart(new_rc)


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------

_COMMAND_LINE_RE = re.compile(
    r'^(\s*)(--)?(\s*)"([^"]*)"(\s*,?\s*)(--.*)?$'
)


def _parse_command_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a line inside the run_once table. Returns None for non-command lines."""
    m = _COMMAND_LINE_RE.match(line)
    if not m:
        return None
    return {
        "indent": m.group(1),
        "comment_prefix": m.group(2) is not None,
        "spaces_after_comment": m.group(3),
        "command": m.group(4),
        "comma_and_trailing": m.group(5),
        "trailing_comment": m.group(6) or "",
        "enabled": m.group(2) is None,
    }


def _enable_line(parsed: Dict[str, Any]) -> str:
    """Build an enabled version of a disabled command line."""
    return (
        parsed["indent"]
        + '"'
        + parsed["command"]
        + '"'
        + parsed["comma_and_trailing"]
        + parsed["trailing_comment"]
    )


def _guess_indent(lines: List[str]) -> str:
    """Return a reasonable indentation string for new commands."""
    for line in lines:
        parsed = _parse_command_line(line)
        if parsed and parsed["enabled"]:
            return parsed["indent"]
    # Fallback to 4 spaces
    return "    "


def _create_minimal_autostart(commands: set) -> None:
    """Create a basic autostart.lua with the given commands."""
    indent = "    "
    cmd_lines = "\n".join(f'{indent}"{c}",' for c in commands)
    content = f"""-- configuration/autostart.lua
local awful = require("awful")
local filesystem = require("gears.filesystem")
local config_dir = filesystem.get_configuration_dir()

-- Autostart windowless processes
local function run_once(cmd_arr)
    for _, cmd in ipairs(cmd_arr) do
        awful.spawn.with_shell(string.format("pgrep -u $USER -fx '%s' > /dev/null || (%s)", cmd, cmd))
    end
end

run_once({{
{cmd_lines}
}})
"""
    _write_autostart(content)