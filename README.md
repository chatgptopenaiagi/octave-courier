# Octave Courier

A small Python API and command-line bridge to a separately installed [GNU Octave](https://octave.org/).

Octave Courier discovers your Octave installation, exchanges finite real matrices
through structured JSON, runs local mathematical scripts and exports PNG plots.
GNU Octave performs the calculations. Octave Courier handles processes, arguments,
data shape, results, errors and timeouts.

This is an independent integration project. It is not an official GNU Octave
distribution, and its packages do not include GNU Octave.

## Start with a matrix

Install GNU Octave, then download a distribution from
[release v0.1.0](https://github.com/chatgptopenaiagi/octave-courier/releases/tag/v0.1.0).
For the Python package, install the downloaded wheel:

```console
python -m pip install ./octave_courier-0.1.0-py3-none-any.whl
octave-courier discover
octave-courier matrix --a "[[1,2],[3,4]]" --b "[[5,6],[7,8]]"
```

The result contains `[[19,22],[43,50]]` with shape `[2,2]`.
The wheel has no third-party Python runtime dependencies. It requires Python 3.10
or later and external GNU Octave 7 or later. The version floor is an interface
requirement, not a claim that every intervening runtime version was tested.
Windows users can instead use
the executable distribution without installing Python.

## Python API

```python
from octave_courier import Octave

octave = Octave()
product = octave.matrix_product([[1, 2], [3, 4]], [[5, 6], [7, 8]])
assert product["result"] == [[19, 22], [43, 50]]

solution = octave.solve([[3, 1], [1, 2]], [[9], [8]])
print(solution["result"])
octave.plot("sine.png")
```

Discovery checks an explicit path, `OCTAVE_EXECUTABLE`, `PATH` and standard
Windows installation directories. To choose a runtime explicitly:

```console
octave-courier --octave /usr/bin/octave-cli doctor
```

## Choose a distribution

| Distribution | Additional software required |
| --- | --- |
| Windows x64 executable or ZIP | GNU Octave; gnuplot for plotting |
| Linux x86_64 launcher archive | Python 3.10+, GNU Octave; gnuplot for plotting |
| Python wheel or source distribution | Python 3.10+, GNU Octave; gnuplot for plotting |

The Linux archive is a Python launcher distribution, not a frozen standalone
executable. The pure-Python wheel is platform independent; that label does not
establish that every platform or Octave version has been tested.
See [release verification](RELEASE-NOTES.md) for exact tested combinations.
ARM64 and macOS are not verified release targets.

| Release environment | Python side | GNU Octave |
| --- | --- | --- |
| Windows 11 x64 | Clean wheel: 3.12.14; frozen build: 3.14.7; source/API checks: 3.14.9 | 11.3.0 |
| Ubuntu 26.04.1 x86_64 under WSL2 | 3.14.4 | 11.1.0 |

Local source/API and installed-wheel checks include real matrix calculations,
linear solves, the fixed demonstrations and PNG export. Release manifests bind
the final packaged-artifact checks to their exact filenames and hashes.

## What v0.1.0 provides

- Matrix multiplication and square linear solves with explicit 2-D shapes.
- Fixed numerical, descriptive-statistics, signal and optimisation demonstrations.
- Runtime information, installed package discovery and PNG export.
- Local script execution with argument lists, optional installed packages and a timeout.
- JSON output, typed Python errors and failure exit codes.

The numeric exchange contract is finite real double precision, with at most
256 rows and 256 columns per input matrix. It does not preserve arbitrary
Octave objects, exact large integers, complex numbers or arbitrary precision.
Executing a supplied script runs trusted local code; it is not a sandbox.

## Documentation

[Getting started](GETTING-STARTED.md) · [Windows installation](INSTALL-WINDOWS.md) ·
[Linux installation](INSTALL-LINUX.md) · [Python API](PYTHON-API.md) ·
[CLI reference](CLI-REFERENCE.md) · [Mathematical examples](MATHEMATICAL-EXAMPLES.md) ·
[Architecture](ARCHITECTURE.md) · [Dependencies](DEPENDENCIES.md) ·
[Limitations](KNOWN-LIMITATIONS.md) · [Contributing](CONTRIBUTING.md)

The original engineering environment catalogued 55 installed Octave packages.
That inventory is not a claim that all packages or their functions are supported
or tested by this public product. The basic demonstrations use Octave core
functions and do not install packages automatically.

Octave Courier is licensed under [MIT](LICENSE). GNU Octave and bundled executable
runtime components retain their own licenses; see [third-party notices](THIRD-PARTY-NOTICES.md)
and [provenance](PROVENANCE.md).
