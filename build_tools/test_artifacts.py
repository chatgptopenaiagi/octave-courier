"""Install and execute actual release artifacts in fresh isolated directories.

Requires a separately installed GNU Octave with plotting prerequisites. The
source distribution may download its declared build dependencies into pip's
temporary build isolation; the core application has no Python dependencies.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
import venv
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def invoke(command, cwd, label, evidence, *, expected=0, timeout=120):
    environment = dict(os.environ)
    for name in ("PYTHONPATH", "PYTHONHOME"):
        environment.pop(name, None)
    began = time.perf_counter()
    process = subprocess.run(command, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    (evidence / (label + ".stdout.txt")).write_text(process.stdout, encoding="utf-8")
    (evidence / (label + ".stderr.txt")).write_text(process.stderr, encoding="utf-8")
    if process.returncode != expected:
        raise RuntimeError(f"{label}: expected exit {expected}, got {process.returncode}: {process.stderr[-1500:]}")
    return {"command": command, "exit_code": process.returncode, "elapsed_ms": round((time.perf_counter()-began)*1000,3)}, process.stdout


def check_cli(command, cwd, evidence, prefix):
    cases = []
    row, text = invoke(command + ["--version"], cwd, prefix + "-version", evidence)
    if "0.1.0" not in text:
        raise RuntimeError("Wrong packaged version")
    cases.append(dict(row, name="version", passed=True))
    row, text = invoke(command + ["matrix", "--a", "[[1,2],[3,4]]", "--b", "[[5,6],[7,8]]"], cwd, prefix+"-matrix", evidence)
    product = json.loads(text)
    if product["result"] != [[19,22],[43,50]]:
        raise RuntimeError("Packaged matrix calculation differs from independent expected result")
    cases.append(dict(row, name="matrix", passed=True))
    row, text = invoke(command + ["solve", "--a", "[[3,1],[1,2]]", "--b", "[[9],[8]]"], cwd, prefix+"-solve", evidence)
    result = json.loads(text)["result"]
    residual = max(abs(3*result[0][0]+result[1][0]-9), abs(result[0][0]+2*result[1][0]-8))
    if residual >= 1e-10:
        raise RuntimeError("Packaged linear solve residual exceeds tolerance")
    cases.append(dict(row, name="solve", passed=True, maximum_residual=residual))
    row, text = invoke(command + ["doctor"], cwd, prefix+"-doctor", evidence, timeout=180)
    doctor = json.loads(text)
    if doctor.get("verified") is not True or len(doctor.get("checks", [])) != 7:
        raise RuntimeError("Packaged doctor did not pass all seven mathematical checks")
    cases.append(dict(row, name="doctor", passed=True, mathematical_checks=7, runtime=doctor.get("runtime")))
    png = cwd / (prefix + "-sine.png")
    row, text = invoke(command + ["plot", "--output", str(png)], cwd, prefix+"-plot", evidence)
    raw = png.read_bytes()
    if len(raw) < 1000 or raw[:8] != b"\x89PNG\r\n\x1a\n" or min(struct.unpack(">II", raw[16:24])) < 1:
        raise RuntimeError("Packaged plot is not a substantive PNG")
    cases.append(dict(row, name="plot", passed=True, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)))
    row, _ = invoke(command + ["matrix", "--a", "[[1,2]]", "--b", "[[1,2]]"], cwd, prefix+"-invalid", evidence, expected=1)
    cases.append(dict(row, name="invalid_input", passed=True))
    script = cwd / (prefix + "-nonzero.m")
    script.write_text("exit(7);\n", encoding="utf-8")
    row, _ = invoke(command + ["run", str(script)], cwd, prefix+"-nonzero", evidence, expected=7)
    cases.append(dict(row, name="nonzero_exit", passed=True))
    script = cwd / (prefix + "-timeout.m")
    script.write_text("pause(30);\n", encoding="utf-8")
    row, _ = invoke(command + ["--timeout", "0.1", "run", str(script)], cwd, prefix+"-timeout", evidence, expected=124, timeout=15)
    cases.append(dict(row, name="timeout", passed=True))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--sdist", type=Path)
    parser.add_argument("--windows-executable", type=Path)
    parser.add_argument("--windows-zip", type=Path)
    parser.add_argument("--linux-archive", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="A new evidence directory")
    args = parser.parse_args()
    if not any((args.wheel,args.sdist,args.windows_executable,args.windows_zip,args.linux_archive)):
        parser.error("Select at least one artifact")
    evidence = args.output.resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    cwd = evidence / "separate-working-directory"
    cwd.mkdir()
    results = []
    for kind, artifact in (("wheel", args.wheel), ("sdist", args.sdist)):
        if artifact is None:
            continue
        artifact = artifact.resolve()
        environment = evidence / (kind + "-venv")
        venv.EnvBuilder(with_pip=True, clear=False, system_site_packages=False).create(environment)
        python = environment / ("Scripts/python.exe" if os.name=="nt" else "bin/python")
        install_command = [str(python), "-m", "pip", "install", "--no-deps"]
        if kind == "wheel":
            install_command.append("--no-index")
        install_command.append(str(artifact))
        install, _ = invoke(install_command, cwd, kind+"-installation", evidence, timeout=300)
        row, text = invoke([str(python), "-I", "-c", "import json,sys,octave_courier; print(json.dumps({'file':octave_courier.__file__,'python':sys.version}))"], cwd, kind+"-import", evidence)
        imported = json.loads(text)
        if not Path(imported["file"]).resolve().is_relative_to(environment.resolve()):
            raise RuntimeError("Package import escaped the fresh installation")
        command = [str(environment / ("Scripts/octave-courier.exe" if os.name=="nt" else "bin/octave-courier"))]
        cases = check_cli(command,cwd,evidence,kind)
        results.append({"kind":kind,"artifact":str(artifact),"artifact_sha256":hashlib.sha256(artifact.read_bytes()).hexdigest(),"installation":install,"import":imported,"cases":cases,"verified":all(c["passed"] for c in cases)})
    if args.windows_executable:
        artifact=args.windows_executable.resolve()
        target=cwd/artifact.name
        shutil.copyfile(artifact,target)
        cases=check_cli([str(target)],cwd,evidence,"windows-exe")
        results.append({"kind":"windows-executable","artifact":str(artifact),"artifact_sha256":hashlib.sha256(artifact.read_bytes()).hexdigest(),"cases":cases,"verified":True})
    if args.windows_zip:
        artifact=args.windows_zip.resolve();extracted=evidence/"windows-zip-extracted"
        with zipfile.ZipFile(artifact) as archive:archive.extractall(extracted)
        executable=next(extracted.glob("*.exe"))
        cases=check_cli([str(executable)],cwd,evidence,"windows-zip")
        results.append({"kind":"windows-zip","artifact":str(artifact),"artifact_sha256":hashlib.sha256(artifact.read_bytes()).hexdigest(),"cases":cases,"verified":True})
    if args.linux_archive:
        if os.name!="posix":raise RuntimeError("Linux distribution must be tested in an actual Linux process")
        artifact=args.linux_archive.resolve();extracted=evidence/"linux-extracted";extracted.mkdir()
        with tarfile.open(artifact) as archive:archive.extractall(extracted,filter="data")
        executable=next(extracted.glob("*/bin/octave-courier"))
        cases=check_cli([str(executable)],cwd,evidence,"linux-launcher")
        results.append({"kind":"linux-launcher","artifact":str(artifact),"artifact_sha256":hashlib.sha256(artifact.read_bytes()).hexdigest(),"cases":cases,"verified":True})
    result={"checked_at":datetime.now(timezone.utc).isoformat(),"verified":all(r["verified"] for r in results),"python":sys.version,"platform":sys.platform,"results":results,"scope":"Actual packaged installations/extractions in new isolated directories, external GNU Octave mathematical and failure/timeout checks; no original source paths imported"}
    (evidence/"result.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"verified":result["verified"],"kinds":[r["kind"] for r in results],"evidence":str(evidence/"result.json")},indent=2))


if __name__=="__main__":main()
