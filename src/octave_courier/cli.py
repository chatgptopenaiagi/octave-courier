"""Command-line interface for the portable Octave Courier API."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import tempfile

from . import __version__
from .engine import Octave, OctaveError, OctaveTimeoutError


def _json(value):
    try:
        return json.loads(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Expected a valid JSON value: " + str(error)) from None


def parser():
    result = argparse.ArgumentParser(prog="octave-courier", description="Python and CLI integration with a separately installed GNU Octave.")
    result.add_argument("--version", action="version", version="%(prog)s " + __version__)
    result.add_argument("--octave", help="Explicit Octave executable (otherwise environment/PATH/standard installation discovery)")
    result.add_argument("--timeout", type=float, default=30, help="Maximum seconds per Octave process (default: 30)")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("discover", help="Find Octave and report the actual runtime version")
    commands.add_parser("packages", help="List installed package registrations; not a package functionality test")
    for name in ("matrix", "solve"):
        command = commands.add_parser(name, help="Multiply matrices" if name == "matrix" else "Solve a square nonsingular linear system")
        command.add_argument("--a", type=_json, required=True, help="JSON two-dimensional finite real matrix")
        command.add_argument("--b", type=_json, required=True, help="JSON two-dimensional finite real matrix")
    compute = commands.add_parser("compute", help="Run a documented fixed mathematical demonstration")
    compute.add_argument("operation", choices=("numerical", "statistics", "signal", "optimization"))
    compute.add_argument("--values", type=_json, help="Optional finite values for the statistics demonstration")
    plot = commands.add_parser("plot", help="Export an owned sine plot to a new PNG file")
    plot.add_argument("--output", type=Path, required=True)
    script = commands.add_parser("run", help="Execute an explicitly supplied trusted .m script; this is not a sandbox")
    script.add_argument("--package", action="append", default=[], help="Load one already-installed package in the child process")
    script.add_argument("--cwd", type=Path, help="Script working directory")
    script.add_argument("script", type=Path)
    script.add_argument("arguments", nargs=argparse.REMAINDER)
    doctor = commands.add_parser("doctor", help="Independently check representative matrix/solve/math/PNG outputs")
    doctor.add_argument("--skip-plot", action="store_true", help="Explicitly skip the graphical export check")
    return result


def doctor(engine, skip_plot=False):
    checks = []
    def record(name, passed, details):
        checks.append({"name": name, "passed": bool(passed), "details": details})
    product = engine.matrix_product([[1, 2], [3, 4]], [[5, 6], [7, 8]])
    record("matrix_product", product["result"] == [[19, 22], [43, 50]], product)
    answer = engine.solve([[3, 1], [1, 2]], [[9], [8]])
    x = answer["result"]
    residual = max(abs(3*x[0][0]+x[1][0]-9), abs(x[0][0]+2*x[1][0]-8))
    record("linear_solve", residual < 1e-10, {"solution": x, "maximum_residual": residual})
    for operation in ("numerical", "statistics", "signal", "optimization"):
        value = engine.compute(operation)
        answer = value["result"]
        if operation == "numerical":
            passed = (abs(answer["integral_x2_0_1"] - 1/3) < 1e-9
                      and abs(answer["integral_sin_0_pi"] - 2) < 1e-9
                      and abs(answer["sqrt2_root"] - math.sqrt(2)) < 1e-8
                      and abs(answer["decay_at_one"] - math.exp(-1)) < 1e-5)
        elif operation == "statistics":
            passed = answer["count"] == 5 and abs(answer["mean"]-3) < 1e-12 and abs(answer["sample_variance"]-2.5) < 1e-12
        elif operation == "signal":
            passed = answer["fft_real"] == [1,1,1,1] and answer["fft_imag"] == [0,0,0,0] and answer["convolution"] == [1,3,2]
        else:
            passed = abs(answer["location"]-3) < 1e-5 and abs(answer["objective"]-7) < 1e-9
        record(operation, passed, value)
    if not skip_plot:
        with tempfile.TemporaryDirectory(prefix="octave-courier-doctor-") as temporary:
            target = Path(temporary) / "sine.png"
            engine.plot(target)
            raw = target.read_bytes()
            valid = len(raw) >= 24 and raw[:8] == b"\x89PNG\r\n\x1a\n"
            dimensions = struct.unpack(">II", raw[16:24]) if valid else (0, 0)
            record("plot", valid and min(dimensions) > 0, {"format": "PNG", "width": dimensions[0], "height": dimensions[1], "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "temporary_file_cleaned": True})
    return {"version": __version__, "runtime": engine.info(), "verified": all(c["passed"] for c in checks), "checks": checks, "plot_skipped": skip_plot, "scope": "Representative fixed operations only; not all installed packages or arbitrary application correctness"}


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        engine = Octave(executable=args.octave, timeout=args.timeout)
        if args.command == "discover": value = engine.info()
        elif args.command == "packages": value = engine.packages()
        elif args.command == "matrix": value = engine.matrix_product(args.a, args.b)
        elif args.command == "solve": value = engine.solve(args.a, args.b)
        elif args.command == "compute":
            if args.values is not None and args.operation != "statistics":
                raise ValueError("--values is accepted only for statistics")
            value = engine.compute(args.operation, **({"values": args.values} if args.values is not None else {}))
        elif args.command == "plot": value = engine.plot(args.output)
        elif args.command == "run":
            arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
            value = engine.run_script(args.script, args=arguments, cwd=args.cwd, packages=args.package)
        else: value = doctor(engine, args.skip_plot)
        print(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2))
        return 0 if not isinstance(value, dict) or value.get("verified", True) else 1
    except (OctaveError, ValueError, OSError) as error:
        details = {"type": type(error).__name__, "message": str(error)}
        if getattr(error, "result", None) is not None: details["result"] = error.result
        print(json.dumps({"error": details}, ensure_ascii=False, allow_nan=False), file=sys.stderr)
        if isinstance(error, OctaveTimeoutError): return 124
        code = getattr(error, "result", {}).get("exit_code", 1) if isinstance(getattr(error, "result", None), dict) else 1
        return code if isinstance(code, int) and 0 < code < 124 else 1


if __name__ == "__main__":
    raise SystemExit(main())
