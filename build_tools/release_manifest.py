"""Create a SHA-256 manifest from verified release artifacts and final Git source.

Verification input is a local JSON object containing environments and one entry
per payload artifact: {filename: {verified: true, checks: [...]}}. It is evidence,
not an instruction to execute commands. Upload only artifacts that passed their
installation or archive-content checks.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    verification = json.loads(args.verification.read_text(encoding="utf-8"))
    version = re.search(r'^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError("A full final Git commit is required")
    payloads = [p for p in sorted(args.dist.iterdir()) if p.is_file() and p.name not in {"artifact-manifest.json", "SHA256SUMS"}]
    if not payloads:
        raise RuntimeError("No distribution artifacts exist")
    checks = verification.get("artifacts", {})
    if set(checks) != {p.name for p in payloads}:
        raise RuntimeError("Verification input must cover exactly the payload filenames")
    artifacts = []
    for path in payloads:
        result = checks[path.name]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if result.get("verified") is not True or not result.get("checks"):
            raise RuntimeError("Artifact lacks passing checks: " + path.name)
        if result.get("sha256") != digest:
            raise RuntimeError("Artifact changed since verification: " + path.name)
        artifacts.append({"filename": path.name, "size": path.stat().st_size, "sha256": digest,
                          "target": result["target"], "distribution_kind": result["distribution_kind"],
                          "verification": {"verified": True, "checks": result["checks"]},
                          "source_commit": commit})
    result = {"schema_version": 1, "product": "Octave Courier", "version": version, "release_tag": "v" + version,
              "source_commit": commit, "created_at": datetime.now(timezone.utc).isoformat(),
              "manifest_platform": platform.platform(), "manifest_python": platform.python_version(),
              "external_dependencies": {"gnu_octave": "Required separately; interface floor >=7, tested versions listed in environments",
                                        "python": "Wheel/Linux launcher >=3.10; Windows executable includes Python",
                                        "plotting": "GNU Octave gnuplot toolkit, gnuplot, suitable fonts and Ghostscript"},
              "environments": verification["environments"], "artifacts": artifacts,
              "limitations": verification.get("limitations", []),
              "checksum_scope": "SHA256SUMS covers every payload and this manifest; it excludes itself to avoid a circular hash"}
    target = args.dist / "artifact-manifest.json"
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    entries = [*payloads, target]
    (args.dist / "SHA256SUMS").write_text("".join(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name + "\n" for p in entries), encoding="utf-8")
    for path in entries:
        if path.stat().st_size <= 0:
            raise RuntimeError("Empty release artifact: " + path.name)
    print(json.dumps({"source_commit": commit, "payload_artifacts": len(payloads), "manifest": str(target)}, indent=2))


if __name__ == "__main__":
    main()
