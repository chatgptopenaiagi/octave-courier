"""Small subprocess and finite-real-double JSON interfaces to GNU Octave.

Derived from the project originator's previously verified local bridge. GNU
Octave remains a separately installed program; no Octave source is bundled.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import struct
import subprocess
import tempfile
import time
from typing import Any

from .discovery import OctaveError, OctaveNotFound, discover

MAX_DIMENSION = 256
MAX_CAPTURE_BYTES = 1_048_576


class ValidationError(ValueError):
    """An input violates the finite-real-double or fixed-operation contract."""


class OctaveExecutionError(OctaveError):
    """The child failed or returned an invalid transport response."""

    def __init__(self, message: str, result: dict[str, Any] | None = None):
        super().__init__(message)
        self.result = result or {}


class OctaveTimeoutError(OctaveExecutionError):
    """The bounded child process exceeded its requested lifetime."""


def _timeout(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 < value <= 3600:
        raise ValidationError("timeout must be finite and in (0, 3600] seconds")
    return float(value)


def _matrix(value: Any, name: str) -> dict[str, Any]:
    if hasattr(value, "tolist"):
        value = value.tolist()
    if not isinstance(value, (tuple, list)) or not 1 <= len(value) <= MAX_DIMENSION:
        raise ValidationError(f"{name} must have 1..{MAX_DIMENSION} rows")
    columns: int | None = None
    values: list[float] = []
    for row in value:
        if not isinstance(row, (tuple, list)) or not 1 <= len(row) <= MAX_DIMENSION:
            raise ValidationError(f"{name} must contain rows of 1..{MAX_DIMENSION} values")
        columns = len(row) if columns is None else columns
        if len(row) != columns:
            raise ValidationError(f"{name} must be rectangular")
        for item in row:
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                raise ValidationError(f"{name} accepts finite real numbers only")
            if isinstance(item, int) and abs(item) > 2**53:
                raise ValidationError(f"{name} integer exceeds the exact IEEE double integer range (+/-2**53)")
            try:
                number = float(item)
            except OverflowError:
                raise ValidationError(f"{name} contains a number outside double precision") from None
            if not math.isfinite(number):
                raise ValidationError(f"{name} accepts finite real numbers only")
            values.append(number)
    return {"rows": len(value), "columns": columns, "values": values}


class _WindowsJob:
    """Own a Windows job so timeout/cleanup terminates the child's descendants."""

    def __init__(self, process: subprocess.Popen):
        self.handle = None
        if os.name != "nt":
            return
        class BasicLimits(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
                        ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]
        class IOCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount", "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]
        class ExtendedLimits(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BasicLimits), ("IoInfo", IOCounters),
                        ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel.CreateJobObjectW.restype = wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.CreateJobObjectW(None, None)
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not handle or not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            if handle:
                kernel.CloseHandle(handle)
            raise OSError(ctypes.get_last_error(), "Cannot create bounded Windows child job")
        if not kernel.AssignProcessToJobObject(handle, wintypes.HANDLE(int(process._handle))):
            error = ctypes.get_last_error()
            kernel.CloseHandle(handle)
            if process.poll() is None:
                raise OSError(error, "Cannot assign Octave process to bounded Windows child job")
            return
        self.kernel, self.handle = kernel, handle

    def close(self):
        if self.handle is not None:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def _kill_group(process: subprocess.Popen, job: _WindowsJob | None):
    if os.name == "nt":
        if job is not None:
            job.close()
        if process.poll() is None:
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=5)


def _capture(stream) -> tuple[str, bool]:
    stream.seek(0)
    data = stream.read(MAX_CAPTURE_BYTES + 1)
    return data[:MAX_CAPTURE_BYTES].decode("utf-8", errors="replace"), len(data) > MAX_CAPTURE_BYTES


def _finite_tree(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(_finite_tree(v) for v in value.values())
    if isinstance(value, list):
        return all(_finite_tree(v) for v in value)
    # jsonencode converts nonfinite numbers to JSON null on supported Octave
    # versions. No response field in our schema needs null, so reject it rather
    # than silently treating numerical overflow as a valid result.
    return isinstance(value, (str, int, bool))


class Octave:
    """Connect to an external GNU Octave >=7 installation using isolated children.

    Every call starts a fresh process with user/site startup files and history
    disabled. Fixed numerical methods accept data only. run_script deliberately
    executes caller-authorized .m code and is not a security sandbox.
    """

    def __init__(self, executable: str | os.PathLike[str] | None = None, timeout: float = 30):
        self.executable = discover(executable)
        self.timeout = _timeout(timeout)
        version_result = self._execute(["--version"], timeout=self.timeout)
        match = re.search(r"GNU Octave[^\r\n]*?version\s+(\d+\.\d+(?:\.\d+)?)", version_result["stdout"], re.IGNORECASE)
        if not match:
            raise OctaveExecutionError("The selected executable did not report a GNU Octave version", version_result)
        self._runtime_version = match.group(1)
        if int(self._runtime_version.split(".")[0]) < 7:
            raise OctaveError("Octave Courier requires GNU Octave 7 or newer")

    @property
    def runtime_version(self) -> str:
        return self._runtime_version

    def info(self) -> dict[str, Any]:
        return {"executable": str(self.executable), "octave_version": self.runtime_version,
                "transport": "finite real IEEE double matrices through shape-tagged JSON files",
                "minimum_octave_version": "7", "maximum_matrix_dimension": MAX_DIMENSION,
                "scope": "Version detection only; packages and mathematical operations have separate checks"}

    def _execute(self, arguments, *, timeout: float, cwd: Path | None = None, env: dict[str, str] | None = None) -> dict[str, Any]:
        seconds = _timeout(timeout)
        environment = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
        if env:
            environment.update(env)
        started, timed_out, process, job = time.perf_counter(), False, None, None
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            try:
                process = subprocess.Popen([str(self.executable), *map(str, arguments)], cwd=cwd, env=environment,
                    stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, shell=False,
                    start_new_session=os.name != "nt",
                    creationflags=(getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)) if os.name == "nt" else 0)
                job = _WindowsJob(process)
                try:
                    process.wait(timeout=seconds)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    _kill_group(process, job)
            except OSError as error:
                if process is not None and process.poll() is None:
                    _kill_group(process, job)
                raise OctaveExecutionError("GNU Octave could not execute: " + str(error)) from error
            finally:
                if job is not None:
                    job.close()
            out, out_truncated = _capture(stdout)
            err, err_truncated = _capture(stderr)
        result = {"exit_code": process.returncode, "stdout": out, "stderr": err, "timed_out": timed_out,
                  "stdout_truncated": out_truncated, "stderr_truncated": err_truncated,
                  "elapsed_ms": round((time.perf_counter() - started) * 1000, 3), "executable": str(self.executable)}
        if timed_out:
            raise OctaveTimeoutError(f"GNU Octave exceeded the {seconds:g} second timeout; owned process group terminated", result)
        if process.returncode:
            raise OctaveExecutionError(f"GNU Octave exited with code {process.returncode}: {err.strip()[-2000:]}", result)
        return result

    def _request(self, operation: str, **parameters) -> dict[str, Any]:
        worker = Path(__file__).with_name("worker.m")
        if not worker.is_file():
            raise OctaveError("Packaged Octave worker.m resource is missing")
        with tempfile.TemporaryDirectory(prefix="octave-courier-") as directory:
            folder = Path(directory)
            source, target = folder / "request.json", folder / "response.json"
            request = {"schema_version": 1, "operation": operation, **parameters}
            source.write_text(json.dumps(request, ensure_ascii=False, allow_nan=False), encoding="utf-8")
            result = self._execute(["--no-gui", "--quiet", "--no-init-file", "--no-site-file", "--no-history", str(worker), str(source), str(target)], timeout=self.timeout, cwd=folder)
            if not target.is_file() or target.stat().st_size > 8_000_000:
                raise OctaveExecutionError("Octave response is absent or exceeds the bounded JSON contract", result)
            try:
                response = json.loads(target.read_text(encoding="utf-8"))
            except (ValueError, UnicodeError) as error:
                raise OctaveExecutionError("Octave response is not valid UTF-8 JSON", result) from error
            if (not isinstance(response, dict) or response.get("schema_version") != 1 or response.get("operation") != operation
                    or response.get("octave_version") != self.runtime_version or not _finite_tree(response)):
                raise OctaveExecutionError("Octave response violates its schema, runtime or finite-value contract", result)
            response.update(elapsed_ms=result["elapsed_ms"], executable=str(self.executable))
            if result["stderr"]:
                response["diagnostics"] = result["stderr"]
            return response

    def _matrix_operation(self, operation: str, a: Any, b: Any) -> dict[str, Any]:
        left, right = _matrix(a, "a"), _matrix(b, "b")
        if operation == "matrix_product":
            if left["columns"] != right["rows"]:
                raise ValidationError("Matrix multiplication requires a.columns == b.rows")
            shape = [left["rows"], right["columns"]]
        else:
            if left["rows"] != left["columns"] or left["rows"] != right["rows"]:
                raise ValidationError("solve requires square a and matching b.rows")
            shape = [left["columns"], right["columns"]]
        response = self._request(operation, a=left, b=right)
        values = response.pop("values", None)
        values = values if isinstance(values, list) else [values]
        if (response.get("shape") != shape or len(values) != shape[0] * shape[1]
                or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values)):
            raise OctaveExecutionError("Octave matrix response has an invalid shape or values")
        response["result"] = [values[i:i + shape[1]] for i in range(0, len(values), shape[1])]
        response["transport_contract_validated"] = True
        return response

    def matrix_product(self, a: Any, b: Any) -> dict[str, Any]:
        return self._matrix_operation("matrix_product", a, b)

    def solve(self, a: Any, b: Any) -> dict[str, Any]:
        return self._matrix_operation("solve", a, b)

    def packages(self) -> dict[str, Any]:
        """Catalog installed package registrations without loading optional packages."""
        return self._request("packages")

    def compute(self, operation: str, **parameters: Any) -> dict[str, Any]:
        """Run a fixed core demonstration: numerical/statistics/signal/optimization.

        statistics accepts a finite numeric matrix values= (default [[1,2,3,4,5]])
        and treats all values as one sample. Other demonstrations accept no data.
        No expression strings or Octave source are accepted through this method.
        """
        if not isinstance(operation, str) or operation not in {"numerical", "statistics", "signal", "optimization"}:
            raise ValidationError("compute operation must be numerical, statistics, signal or optimization")
        if operation == "statistics":
            if set(parameters) - {"values"}:
                raise ValidationError("statistics accepts only values")
            values = _matrix(parameters.get("values", [[1, 2, 3, 4, 5]]), "values")
            if len(values["values"]) < 2:
                raise ValidationError("Sample statistics requires at least two values")
            parameters = {"data": values}
        elif parameters:
            raise ValidationError(operation + " is a fixed demonstration and accepts no parameters")
        return self._request(operation, **parameters)

    def plot(self, output: str | os.PathLike[str]) -> dict[str, Any]:
        """Export one owned sine PNG. Existing destination files are preserved."""
        destination = Path(output).expanduser().resolve()
        if destination.suffix.lower() != ".png":
            raise ValidationError("Plot output must have a .png suffix")
        if destination.exists():
            raise ValidationError("Plot output already exists; choose a new file")
        if not destination.parent.is_dir():
            raise ValidationError("Plot output parent directory must already exist")
        with tempfile.TemporaryDirectory(prefix="octave-courier-plot-") as directory:
            temporary_png = Path(directory) / "plot.png"
            response = self._request("plot", output=str(temporary_png))
            if not temporary_png.is_file():
                raise OctaveExecutionError("Octave did not create a plot artifact")
            data = temporary_png.read_bytes()
            if len(data) < 1000 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
                raise OctaveExecutionError("Octave plot output is not a substantive PNG")
            width, height = struct.unpack(">II", data[16:24])
            if not width or not height:
                raise OctaveExecutionError("Octave PNG dimensions are invalid")
            with destination.open("xb") as handle:
                handle.write(data)
            response.update(output=str(destination), bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), width=width, height=height)
            return response

    def run_script(self, path: str | os.PathLike[str], args=(), *, timeout: float | None = None,
                   cwd: str | os.PathLike[str] | None = None, packages=()) -> dict[str, Any]:
        """Execute explicitly supplied .m code, with literal argv and no shell.

        User scripts have the same filesystem/network rights as Octave Courier.
        Only owned child processes are terminated; this API is not a sandbox.
        Captured stdout/stderr are limited to 1 MiB each, with truncation flags.
        """
        script = Path(path).expanduser().resolve()
        if script.suffix.lower() != ".m" or not script.is_file():
            raise ValidationError("Script path must identify an existing .m file")
        if isinstance(args, (str, bytes)) or not isinstance(args, (tuple, list)) or any(not isinstance(arg, str) or "\x00" in arg for arg in args):
            raise ValidationError("args must be a list/tuple of NUL-free strings")
        if isinstance(packages, (str, bytes)) or not isinstance(packages, (tuple, list)) or any(not isinstance(name, str) or re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name) is None for name in packages):
            raise ValidationError("packages must be installed package names in a list/tuple")
        working = Path(cwd).expanduser().resolve() if cwd is not None else script.parent
        if not working.is_dir():
            raise ValidationError("cwd must identify an existing directory")
        seconds = self.timeout if timeout is None else _timeout(timeout)
        source_hash = hashlib.sha256(script.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="octave-courier-script-") as directory:
            wrapper = Path(directory) / "invoke.m"
            prelude = ["more off;"] + ["pkg ('load', '" + name + "');" for name in packages]
            prelude.append('source (getenv ("OCTAVE_COURIER_SCRIPT"));')
            wrapper.write_text("\n".join(prelude) + "\n", encoding="utf-8")
            result = self._execute(["--no-gui", "--quiet", "--no-init-file", "--no-site-file", "--no-history", str(wrapper), *args],
                                   timeout=seconds, cwd=working, env={"OCTAVE_COURIER_SCRIPT": str(script)})
        result.update(script=str(script), script_sha256=source_hash,
                      script_changed_during_execution=not script.is_file() or hashlib.sha256(script.read_bytes()).hexdigest() != source_hash,
                      octave_version=self.runtime_version)
        return result
