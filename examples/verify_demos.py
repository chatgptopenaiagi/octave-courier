"""Verify the documented fixed demonstrations with independent expectations."""
import argparse
import json
import math
from octave_courier import Octave


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--octave", help="Optional installed GNU Octave executable")
    parser.add_argument("--plot", help="Optional new PNG output path")
    args = parser.parse_args()
    octave = Octave(executable=args.octave)
    numerical = octave.compute("numerical")["result"]
    assert abs(numerical["integral_sin_0_pi"] - 2) < 1e-9
    assert abs(numerical["integral_x2_0_1"] - 1/3) < 1e-9
    assert abs(numerical["sqrt2_root"] - math.sqrt(2)) < 1e-8
    assert abs(numerical["decay_at_one"] - math.exp(-1)) < 1e-5
    statistics = octave.compute("statistics", values=[[1, 2, 3, 4]])["result"]
    assert statistics["count"] == 4 and abs(statistics["mean"] - 2.5) < 1e-12
    assert abs(statistics["sample_variance"] - 5/3) < 1e-12
    signal = octave.compute("signal")["result"]
    assert signal["fft_real"] == [1, 1, 1, 1]
    assert signal["fft_imag"] == [0, 0, 0, 0]
    assert signal["fir_filter"] == [0.5, 1, 1, 1]
    assert signal["convolution"] == [1, 3, 2]
    optimization = octave.compute("optimization")["result"]
    assert abs(optimization["location"] - 3) < 1e-5
    assert abs(optimization["objective"] - 7) < 1e-9
    result = {"verified": True, "octave_version": octave.runtime_version,
              "numerical": numerical, "statistics": statistics,
              "signal": signal, "optimization": optimization}
    if args.plot:
        result["plot"] = octave.plot(args.plot)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
