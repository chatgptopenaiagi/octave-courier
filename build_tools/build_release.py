"""Build release artifacts with existing Python build/PyInstaller tooling.

GNU Octave is a separately installed runtime and is never bundled here.
Run this script with the interpreter whose build tools you intend to use.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import uuid
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PRIVATE = ROOT / ".release"


def product_version():
    match = re.search(r'^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M)
    if not match:
        raise RuntimeError("Package version was not found in pyproject.toml")
    return match.group(1)


def run(command, label, *, timeout=300):
    began = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    folder = PRIVATE / "build-logs"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / (label + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
    (folder / (label + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{label} failed with exit {result.returncode}; inspect {folder}")
    return {"command": command, "started_at": began, "exit_code": result.returncode, "log_directory": str(folder)}


def collect_frozen_licenses():
    folder = PRIVATE / "frozen-licenses"
    folder.mkdir(parents=True, exist_ok=True)
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if not python_license.is_file():
        raise RuntimeError("The build Python distribution's actual LICENSE.txt is required")
    shutil.copyfile(python_license, folder / "LICENSE-Python.txt")
    for project, suffix, target in [
        ("pyinstaller", "COPYING.txt", "COPYING-PyInstaller.txt"),
        ("pyinstaller-hooks-contrib", "LICENSE", "LICENSE-PyInstaller-hooks.txt"),
    ]:
        distribution = importlib.metadata.distribution(project)
        source = next((distribution.locate_file(file) for file in distribution.files or () if str(file).replace("\\", "/").endswith("/licenses/" + suffix)), None)
        if source is None or not Path(source).is_file():
            raise RuntimeError(f"Actual installed license is unavailable for {project}")
        shutil.copyfile(source, folder / target)
    for name in ("LICENSE", "THIRD-PARTY-NOTICES.md"):
        shutil.copyfile(ROOT / name, folder / name)
    return folder


def windows_executable(version):
    if sys.platform != "win32" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise RuntimeError("The Windows x86_64 asset must be built on Windows x86_64")
    licenses = collect_frozen_licenses()
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile", "--noupx", "--name", "octave-courier",
               "--distpath", str(PRIVATE / "frozen"), "--workpath", str(PRIVATE / "pyinstaller-work"),
               "--specpath", str(PRIVATE / "spec"), "--paths", str(ROOT / "src"),
               "--add-data", str(ROOT / "src/octave_courier/worker.m") + ":octave_courier",
               "--add-data", str(licenses) + ":license-data", str(ROOT / "build_tools/entry.py")]
    receipt = run(command, "windows-pyinstaller", timeout=600)
    target = DIST / f"octave-courier-v{version}-windows-x86_64.exe"
    shutil.copyfile(PRIVATE / "frozen/octave-courier.exe", target)
    archive = DIST / f"octave-courier-v{version}-windows-x86_64.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        zipped.write(target, target.name)
        for license_file in sorted(licenses.iterdir()):
            zipped.write(license_file, "licenses/" + license_file.name)
        for name in ("README.md", "INSTALL-WINDOWS.md", "CLI-REFERENCE.md", "RELEASE-NOTES.md"):
            if (ROOT / name).is_file():
                zipped.write(ROOT / name, name)
    receipt.update(artifacts=[str(target), str(archive)], bundled_python=sys.version, pyinstaller=importlib.metadata.version("pyinstaller"), external_octave=True)
    return receipt


def linux_launcher(version):
    prefix = f"octave-courier-v{version}-linux-x86_64"
    # A new private staging directory preserves earlier build evidence and
    # avoids deleting or overwriting a prior extracted distribution.
    stage = PRIVATE / "linux-stage" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex[:8]) / prefix
    (stage / "bin").mkdir(parents=True)
    (stage / "lib").mkdir()
    shutil.copytree(ROOT / "src/octave_courier", stage / "lib/octave_courier", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    launcher = stage / "bin/octave-courier"
    launcher.write_text("#!/usr/bin/env python3\nfrom pathlib import Path\nimport sys\nsys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))\nfrom octave_courier.cli import main\nraise SystemExit(main())\n", encoding="utf-8", newline="\n")
    for name in ("LICENSE", "THIRD-PARTY-NOTICES.md", "README.md", "INSTALL-LINUX.md", "CLI-REFERENCE.md", "RELEASE-NOTES.md"):
        if (ROOT / name).is_file():
            shutil.copyfile(ROOT / name, stage / name)
    archive = DIST / (prefix + ".tar.gz")
    with tarfile.open(archive, "w:gz", format=tarfile.PAX_FORMAT) as tar:
        def mode(info):
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mode = 0o755 if info.isdir() or info.name.endswith("/bin/octave-courier") else 0o644
            return info
        tar.add(stage, arcname=prefix, filter=mode)
    return {"artifacts": [str(archive)], "distribution_kind": "Portable Python source launcher; external Python >=3.10 and GNU Octave required", "target": "Linux x86_64", "cross_platform_source": True,
            "source_hashes": {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stage.rglob("*")) if p.is_file()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-packages", action="store_true", help="Build the wheel and sdist with installed build tooling")
    parser.add_argument("--windows-executable", action="store_true", help="Build a Windows x86_64 one-file executable and ZIP")
    parser.add_argument("--linux-launcher", action="store_true", help="Package the Linux Python launcher (test it on Linux separately)")
    args = parser.parse_args()
    if not any(vars(args).values()):
        parser.error("Select at least one artifact type")
    DIST.mkdir(exist_ok=True)
    PRIVATE.mkdir(exist_ok=True)
    version = product_version()
    receipts = []
    if args.python_packages:
        receipts.append(run([sys.executable, "-m", "build", "--no-isolation", "--outdir", str(DIST)], "python-packages"))
    if args.windows_executable:
        receipts.append(windows_executable(version))
    if args.linux_launcher:
        receipts.append(linux_launcher(version))
    result = {"version": version, "built_at": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(), "python": sys.version, "receipts": receipts,
              "artifacts": [{"filename": p.name, "size": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(DIST.iterdir()) if p.is_file()]}
    encoded = json.dumps(result, indent=2) + "\n"
    (PRIVATE / "build-receipt.json").write_text(encoded, encoding="utf-8")
    snapshots = PRIVATE / "build-receipts"
    snapshots.mkdir(exist_ok=True)
    (snapshots / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")).write_text(encoded, encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
