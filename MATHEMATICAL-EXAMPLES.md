# Mathematical examples

These examples use GNU Octave core functionality. They do not require all of the
optional packages found in the original engineering environment.

## Matrix multiplication

```console
octave-courier matrix --a "[[1,2],[3,4]]" --b "[[5,6],[7,8]]"
```

Expected result: `[[19,22],[43,50]]`. The
[independent Python example](examples/python_api.py) checks the exact integers.

## Linear equations

```console
octave-courier solve --a "[[3,1],[1,2]]" --b "[[9],[8]]"
```

Expected result: `[[2],[3]]`. Check the residual `A*x-b`, not only the shape
or process exit code. The Python example calculates it without a third-party
library and requires its maximum absolute entry to be below `1e-10`.

## Numerical analysis

```console
octave-courier compute numerical
```

The fixed demonstration integrates `sin(x)` from 0 to pi (expected 2) and `x^2`
from 0 to 1 (expected 1/3), finds the root `sqrt(2)` and solves the decay ODE
`y'=-y`, `y(0)=1` at time 1 (expected `exp(-1)`). The
[verification example](examples/verify_demos.py) checks these independent answers.

## Statistics

```console
octave-courier compute statistics --values "[[1,2,3,4]]"
```

The arithmetic mean is `2.5`. Descriptive statistics here are core Octave
functions; this example is not a claim about every function in the optional
`statistics` package.

## Signal processing

```console
octave-courier compute signal
```

An impulse FFT has real part `[1,1,1,1]` and imaginary part `[0,0,0,0]`.
The FIR output is `[0.5,1,1,1]`; convolution of `[1,2]` and `[1,1]` is `[1,3,2]`.
Core signal functions
are distinct from the optional `signal` package's complete function set.

## Optimisation

```console
octave-courier compute optimization
```

The bounded demonstration minimises `(x-3)^2+7` on `[-5,7]`. It checks that
the minimum is at 3 with objective value 7, rather than accepting a successful
process exit as proof that an optimisation problem was solved correctly.

## PNG plotting

```console
octave-courier plot --output sine.png
```

The result is an actual PNG file. Plotting requires the gnuplot Octave graphics
backend and its printing dependencies. It does not require opening the interactive
Octave GUI. The release tests check the PNG signature and dimensions.

## Python integration

```console
python examples/python_api.py
python examples/verify_demos.py
```

The examples import the installed package. They do not reference a source tree
or private development directory.

## Script arguments and failures

```console
octave-courier run examples/argv.m "hello world"
octave-courier matrix --a "[[1,2]]" --b "[[1,2]]"
octave-courier run examples/nonzero.m
octave-courier --timeout 0.1 run examples/slow.m
```

The final three commands are expected to fail: incompatible dimensions,
an explicit nonzero exit and a timeout. [failure_handling.py](examples/failure_handling.py)
demonstrates catching failures through the Python API. Scripts are trusted local
code, not sandboxed requests.

## Cross-platform scope

The same API and mathematical commands are used on Windows and Linux. Exact
runtime/platform execution results belong in [release notes](RELEASE-NOTES.md),
with separate clean-install evidence for each artifact. No Linux ARM64 claim is
made from a Windows or x86_64 test.
