"""Check the installed Python API without NumPy or a source-tree import."""
import argparse
import json
from octave_courier import Octave


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--octave", help="Optional installed GNU Octave executable")
    parser.add_argument("--plot", help="Optional new PNG output path")
    args = parser.parse_args()
    octave = Octave(executable=args.octave)
    product = octave.matrix_product([[1, 2], [3, 4]], [[5, 6], [7, 8]])
    assert product["shape"] == [2, 2]
    assert product["result"] == [[19, 22], [43, 50]]
    solution = octave.solve([[3, 1], [1, 2]], [[9], [8]])
    x = solution["result"]
    assert solution["shape"] == [2, 1]
    residual = max(abs(3*x[0][0] + x[1][0] - 9), abs(x[0][0] + 2*x[1][0] - 8))
    assert residual < 1e-10
    result = {"matrix_product": product["result"], "solution": x,
              "maximum_residual": residual, "octave_version": octave.runtime_version,
              "verified": True}
    if args.plot:
        result["plot"] = octave.plot(args.plot)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
