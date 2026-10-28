"""Bounded discovery of an independently installed GNU Octave executable."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil


class OctaveError(RuntimeError):
    """Base error for Octave Courier runtime failures."""


class OctaveNotFound(OctaveError):
    """No usable executable was found at the requested/discovered location."""


def _candidate(value: str | os.PathLike[str]) -> Path | None:
    try:
        text = os.fspath(value)
        expanded = Path(text).expanduser()
        if expanded.is_file() and (os.name == "nt" or os.access(expanded, os.X_OK)):
            return expanded.resolve()
        located = shutil.which(text)
        return Path(located).resolve() if located and Path(located).is_file() else None
    except (OSError, TypeError, ValueError):
        return None


def _version_key(path: Path) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", path.name))


def discover(executable: str | os.PathLike[str] | None = None) -> Path:
    """Find Octave by explicit path, OCTAVE_EXECUTABLE, PATH, then Windows defaults.

    Explicit arguments and environment overrides are authoritative: an invalid
    override raises rather than silently executing a different installation.
    Discovery never installs software or enumerates arbitrary drive contents.
    """
    if executable is not None:
        found = _candidate(executable)
        if found is None:
            raise OctaveNotFound("The explicit GNU Octave executable is unavailable: " + os.fspath(executable))
        return found
    override = os.environ.get("OCTAVE_EXECUTABLE")
    if override:
        found = _candidate(override)
        if found is None:
            raise OctaveNotFound("OCTAVE_EXECUTABLE is unavailable: " + override)
        return found
    for name in ("octave-cli", "octave"):
        located = shutil.which(name)
        found = _candidate(located) if located else None
        if found is not None:
            return found
    if os.name == "nt":
        roots = dict.fromkeys(os.environ.get(name, "") for name in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"))
        for value in roots:
            if not value:
                continue
            for base in (Path(value) / "GNU Octave", Path(value) / "Octave"):
                if not base.is_dir():
                    continue
                for install in sorted(base.glob("Octave-*"), key=_version_key, reverse=True):
                    for relative in ("mingw64/bin/octave-cli.exe", "bin/octave-cli.exe", "mingw64/bin/octave.exe", "bin/octave.exe"):
                        found = _candidate(install / relative)
                        if found is not None:
                            return found
    raise OctaveNotFound("GNU Octave was not found. Install it separately and put octave-cli on PATH, set OCTAVE_EXECUTABLE, or pass executable=.")
