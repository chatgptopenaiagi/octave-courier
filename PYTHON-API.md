# Python API

```python
from octave_courier import Octave, discover

path = discover()  # explicit path, environment, PATH, then standard Windows roots
octave = Octave(executable=path, timeout=30)
print(octave.runtime_version)
print(octave.info())
print(octave.packages())
```

`Octave(executable=None, timeout=30)` selects an external GNU Octave 7+ runtime.
The version floor is separate from release-tested versions. The timeout
is a process time limit in seconds, finite and in `(0, 3600]`. A new Octave process is used for each
operation; variables and package loads are not shared between calls.

## Matrix operations

```python
result = octave.matrix_product([[1, 2], [3, 4]], [[5, 6], [7, 8]])
assert result["shape"] == [2, 2]
assert result["result"] == [[19, 22], [43, 50]]

solution = octave.solve([[3, 1], [1, 2]], [[9], [8]])
assert solution["shape"] == [2, 1]
```

Inputs are rectangular two-dimensional sequences of finite real numbers, with
1–256 rows and columns. NumPy arrays can be supplied through the public
`tolist()` conversion when NumPy is installed; NumPy is optional.
Booleans, complex values, empty or ragged matrices, NaN and infinity are rejected.

Integer inputs outside the exact double integer range `[-2**53, 2**53]` are
rejected. Accepted values are converted to double precision; floating-point
arithmetic still has rounding error. This is not exact decimal or arbitrary-precision
transport. Row, column and scalar-matrix shapes are retained
explicitly. A solve requires square `a`, matching rows in `b` and a numerically
acceptable nonsingular system. Independently check residuals and conditioning
for your application's requirements.

## Fixed demonstrations

```python
numerical = octave.compute("numerical")
statistics = octave.compute("statistics", values=[[1, 2, 3, 4]])
signal = octave.compute("signal")
minimum = octave.compute("optimization")
```

The `values` argument is a two-dimensional matrix; all entries are treated as
one sample and at least two entries are required. These are bounded, implemented demonstrations rather than a general expression
evaluator. They use Octave core functions. Their result dictionaries include
the numerical outputs and runtime information; consult
[the mathematical examples](MATHEMATICAL-EXAMPLES.md) for the independent checks.

## Plotting

```python
plot = octave.plot("sine.png")
```

PNG export uses an owned figure explicitly bound to GNU Octave's gnuplot backend. GNU Octave's
graphics/printing dependencies must be installed. A PNG file result does not
establish interactive GUI functionality. Use a new output path.

## Local scripts

```python
execution = octave.run_script(
    "analysis.m",
    args=("input.csv", "output.csv"),
    timeout=20,
    packages=("signal",),
)
print(execution["stdout"])
```

The package names refer to packages already installed for the selected Octave.
They are loaded in the child process only. Site/user startup files and command
history are disabled. Arguments are passed as an argument vector, without a
command shell. Scripts still have the permissions of the current account and
may access files or networks. Run scripts from sources you trust.

## Errors

The package exports `OctaveError`, `OctaveNotFound`, `OctaveExecutionError`,
`OctaveTimeoutError` and `ValidationError`. `ValidationError` is also a
`ValueError`. Nonzero child exits raise an execution error; timeouts use a
distinct error. Execution errors carry the captured result for diagnosis,
including exit code, stdout and stderr where available. Captured script output
is limited to 1 MiB for each stream, with truncation indicators.

```python
from octave_courier import Octave, OctaveError

try:
    Octave().matrix_product([[1, 2]], [[1, 2]])
except (OctaveError, ValueError) as error:
    print(type(error).__name__, str(error))
```

Successful JSON transport and a zero exit code validate the interface contract.
They are not proof of correctness for an arbitrary mathematical problem.
