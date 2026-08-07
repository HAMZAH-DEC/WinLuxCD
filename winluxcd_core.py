"""Path conversion logic shared by the CLI tests and the Windows GUI."""

import os
import subprocess
from typing import Callable


class PathConversionError(ValueError):
    """Raised when the supplied text is not a convertible path."""


PATH_HINT = (
    "Use a Windows path (C:\\...), a UNC path (\\\\server\\share), "
    "or a WSL path (/home/...)."
)


def normalize_input(raw_input: str) -> str:
    value = raw_input.strip()
    if len(value) >= 2 and (
        (value[0] == '"' and value[-1] == '"')
        or (value[0] == "'" and value[-1] == "'")
    ):
        value = value[1:-1].strip()
    return value


def looks_like_path(value: str) -> bool:
    if not value:
        return False
    has_drive = (
        len(value) >= 3
        and value[0].isalpha()
        and value[1] == ":"
        and value[2] in "\\/"
    )
    return has_drive or value.startswith("/") or value.startswith("\\\\")


def format_cd_command(wsl_path: str) -> str:
    escaped = (
        wsl_path.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("$", "\\$")
        .replace("`", "\\`")
    )
    return 'cd "{}"'.format(escaped)


def convert_to_wsl(raw_input: str, windows_runner: Callable[[str], str]) -> tuple[str, str]:
    value = normalize_input(raw_input)
    if not value:
        raise PathConversionError("Enter a Windows or WSL path.")
    if not looks_like_path(value):
        preview = value.replace("\r", " ").replace("\n", " ")[:60]
        if len(value) > 60:
            preview += "..."
        raise PathConversionError(
            'Input does not look like a path: "{}". {}'.format(preview, PATH_HINT)
        )

    slash_path = value.replace("\\", "/")
    if slash_path.startswith("//"):
        wsl_path = slash_path
    elif value.startswith("/"):
        wsl_path = value
    else:
        wsl_path = (windows_runner(slash_path) or "").strip()
        if not wsl_path:
            raise PathConversionError("WSL returned an empty path.")

    return wsl_path, format_cd_command(wsl_path)


def run_wslpath(windows_path: str) -> str:
    """Run wslpath with safe argument handling and a small child PATH."""
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    wsl_exe = os.path.join(system_root, "System32", "wsl.exe")
    if not os.path.exists(wsl_exe):
        wsl_exe = "wsl.exe"

    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join(
        (os.path.join(system_root, "System32"), system_root)
    )
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        completed = subprocess.run(
            [wsl_exe, "wslpath", "-u", windows_path],
            capture_output=True,
            text=True,
            env=environment,
            creationflags=creationflags,
            check=False,
        )
    except OSError as exc:
        raise PathConversionError(
            "WSL could not be started. Confirm that WSL is installed and available as wsl.exe."
        ) from exc

    output = completed.stdout.strip()
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "wslpath returned exit code {}.".format(
            completed.returncode
        )
        raise PathConversionError("WSL could not convert the path. " + detail)
    if not output:
        raise PathConversionError("WSL returned an empty path.")
    return output
