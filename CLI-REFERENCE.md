# Command-line reference

```text
octave-courier [--octave PATH] [--timeout SECONDS] COMMAND ...
```

Place global options before the command. The command-line entry point and
`python -m octave_courier` expose the same interface. Normal results are JSON.

| Command | Purpose |
| --- | --- |
| `--version` | Print the Octave Courier product version |
| `discover` | Find the external executable and inspect runtime information |
| `packages` | List packages registered in the selected Octave installation |
| `matrix --a JSON --b JSON` | Multiply two rectangular matrices |
| `solve --a JSON --b JSON` | Solve a square nonsingular linear system |
| `compute numerical` | Run the representative numerical calculation |
| `compute statistics [--values JSON]` | Calculate descriptive statistics |
| `compute signal` | Run the representative signal-processing calculation |
| `compute optimization` | Run the representative bounded minimisation |
| `plot --output PATH` | Export a sine plot as PNG |
| `run [--package NAME] [--cwd DIR] SCRIPT [ARG ...]` | Execute a trusted local `.m` script |
| `doctor [--skip-plot]` | Run the built-in representative checks, including plotting unless explicitly skipped |

Examples use JSON arrays, not Octave expressions:

```console
octave-courier matrix --a "[[1,2],[3,4]]" --b "[[5,6],[7,8]]"
octave-courier solve --a "[[3,1],[1,2]]" --b "[[9],[8]]"
octave-courier compute statistics --values "[[1,2,3,4]]"
octave-courier --timeout 20 plot --output sine.png
octave-courier run examples/argv.m "an argument with spaces"
```

Arguments following the script filename belong to the script. Put `run`
options such as `--package signal` before that filename. Use `--help` on the
program or a command for its current argument grammar.

## Discovery

The selection order is an explicit `--octave` path, the
`OCTAVE_EXECUTABLE` environment variable, executables on `PATH`, then bounded
standard Windows installation roots. There is no dependency on the original
engineering workstation or a user's home directory.

## Results and failures

Matrix responses keep the result and shape separately. Script execution captures
stdout, stderr and exit status. Invalid input, unavailable executables, nonzero
Octave exits and timeouts produce a failure exit status and a diagnostic.
Exit codes are 0 for success, 1 for a general execution/validation failure,
2 for command-line syntax errors and 124 for timeout. A positive Octave exit code
below 124 is propagated; other child failure codes map to 1. A skipped plot check
is reported explicitly by `doctor --skip-plot`.

Do not treat a script's zero exit code as a mathematical assertion. Build checks
such as Octave `assert(...)` into scripts where appropriate, and validate their
results independently.
