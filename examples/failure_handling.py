"""Demonstrate expected invalid-input, nonzero-exit and timeout failures."""
import argparse
import json
from pathlib import Path
import tempfile
from octave_courier import Octave, ValidationError, OctaveExecutionError, OctaveTimeoutError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--octave", help="Optional installed GNU Octave executable")
    args = parser.parse_args()
    octave = Octave(executable=args.octave)
    checks = []
    try:
        octave.matrix_product([[1, 2]], [[1, 2]])
    except ValidationError:
        checks.append("incompatible_dimensions_rejected")
    with tempfile.TemporaryDirectory(prefix="octave-courier-example-") as temporary:
        folder = Path(temporary)
        failure = folder / "nonzero.m"
        failure.write_text("exit(7);\n", encoding="utf-8")
        try:
            octave.run_script(failure)
        except OctaveExecutionError as error:
            assert error.result["exit_code"] == 7
            checks.append("nonzero_exit_preserved")
        slow = folder / "slow.m"
        slow.write_text("pause(20);\n", encoding="utf-8")
        try:
            octave.run_script(slow, timeout=0.2)
        except OctaveTimeoutError:
            checks.append("timeout_reported")
    assert len(checks) == 3
    print(json.dumps({"verified": True, "expected_failures_checked": checks}, indent=2))


if __name__ == "__main__":
    main()
