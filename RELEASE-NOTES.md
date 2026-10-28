# Octave Courier v0.1.0

Initial independent release of a Python API and CLI for an external GNU Octave
installation. The project is not an official GNU Octave distribution.

## Downloads

| Asset | Use |
| --- | --- |
| `octave-courier-v0.1.0-windows-x86_64.exe` | Windows x64 CLI with its Python runtime; external Octave required |
| `octave-courier-v0.1.0-windows-x86_64.zip` | Windows distribution with executable, documentation and notices |
| `octave-courier-v0.1.0-linux-x86_64.tar.gz` | Linux launcher/package; external Python 3.10+ and Octave required |
| `octave_courier-0.1.0-py3-none-any.whl` | Platform-independent pure-Python wheel |
| `octave_courier-0.1.0.tar.gz` | Python source distribution |
| `octave-courier-v0.1.0-source.tar.gz` | Public source archive |
| `octave-courier-v0.1.0-examples.zip` | Mathematical scripts and Python examples |
| `SHA256SUMS` and artifact manifest | Artifact names, sizes, SHA-256 and source-commit binding |

Install from these release assets or from the public source repository. A PyPI
publication is not claimed. Verify downloaded files against the checksum manifest.

## Verification scope

The release checks the installed wheel/source package and extracted distributions,
including real mathematical execution and PNG generation. Exact tested Python,
GNU Octave and platform versions are recorded in the machine-readable release
manifest and final release report.

| Environment | Python | GNU Octave | Verification scope |
| --- | --- | --- | --- |
| Windows 11 x64, installed wheel | 3.12.14 | 11.3.0 | Clean environment, 32 tests, installed CLI, package discovery and all 7 doctor checks |
| Windows 11 x64, source/API | 3.14.9 | 11.3.0 | Unit/integration checks, public Python examples and mathematical/PNG outputs |
| Windows x64 executable build | 3.14.7 embedded | External 11.3.0 | PyInstaller 6.22.3 build; final executable/ZIP checks recorded by artifact hash in the manifest |
| Ubuntu 26.04.1 x86_64 under WSL2 | 3.14.4 | 11.1.0 | All 7 source doctor checks, including real PNG export; clean artifact checks recorded by hash in the manifest |

The seven doctor checks are matrix multiplication, linear solve, numerical
analysis, statistics, signal processing, optimisation and PNG plotting. Linux
headless plotting requires the documented gnuplot, fonts and Ghostscript
dependencies. Missing font and `gs` conditions were repaired in the test
environment before recording the successful PNG check.

The package requirement is Python 3.10 or later. That requirement is distinct
from the exact Python versions actually executed for this release. Windows x64
and Linux x86_64 are release targets; Linux ARM64 and macOS are unverified.

The originating engineering integration catalogued 55 Octave packages and
passed selected representative checks. Those inherited counts do not certify
all packages and are not substituted for tests of the new public artifacts.

## Included functionality

Runtime discovery, installed package listing, matrix multiplication, square
linear solve, fixed numerical/statistical/signal/optimisation demonstrations,
trusted local script execution, failure propagation, process timeout and PNG export.
The base package uses Python's standard library. There is no MCP server in v0.1.0.

## Limitations

GNU Octave is never bundled. Plotting requires the gnuplot backend and its
printing dependencies. JSON exchange covers finite real double matrices with
explicit 2-D shape, not arbitrary Octave objects. Script execution is trusted
local code, not a sandbox. See [Known limitations](KNOWN-LIMITATIONS.md).
