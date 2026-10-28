"""Check release archive safety/content and emit SHA-256 values without installing."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import sys
import tarfile
import zipfile


def safe(name):
    path = PurePosixPath(name.replace("\\", "/"))
    return not path.is_absolute() and ".." not in path.parts and not (path.parts and ":" in path.parts[0])


def main():
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    rows = []
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        names = None
        if path.suffix in {".zip", ".whl"}:
            with zipfile.ZipFile(path) as archive:
                assert archive.testzip() is None, path
                names = archive.namelist()
        elif path.name.endswith(".tar.gz"):
            with tarfile.open(path) as archive:
                members = archive.getmembers()
                assert not any(m.issym() or m.islnk() for m in members), path
                names = [m.name for m in members]
        if names is not None:
            assert names and all(safe(name) for name in names), path
            if path.suffix == ".whl":
                assert "octave_courier/worker.m" in names, path
                assert any(name.endswith("/METADATA") for name in names), path
            if "linux-x86_64" in path.name:
                assert any(name.endswith("/bin/octave-courier") for name in names), path
                assert any(name.endswith("/lib/octave_courier/worker.m") for name in names), path
            if "windows-x86_64" in path.name and path.suffix == ".zip":
                assert any(name.endswith(".exe") for name in names), path
                assert "licenses/LICENSE-Python.txt" in names, path
        rows.append({"filename": path.name, "size": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "archive_entries": len(names) if names is not None else None})
    assert rows, "No artifacts were found"
    print(json.dumps({"verified": True, "artifacts": rows}, indent=2))


if __name__ == "__main__":
    main()
