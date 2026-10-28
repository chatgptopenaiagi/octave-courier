# Dependencies

| Component | Required for | Distribution policy |
| --- | --- | --- |
| Python 3.10+ | Wheel, source install and Linux launcher | Installed separately; Windows frozen executable includes its own runtime |
| GNU Octave 7+ | Mathematical operations and scripts | Installed separately; never bundled by this release |
| GNU Octave gnuplot backend, fonts and Ghostscript | PNG export and the plotting part of `doctor` | Use your Octave/distribution packages |
| `setuptools` and `wheel` | Building the Python source distribution | Build dependencies, not core runtime dependencies |
| PyInstaller | Producing the Windows executable | Build dependency only |

The core Python package uses the standard library. NumPy arrays can be converted
through `tolist()`, but NumPy, SciPy, SymPy, pandas, databases, Office and MCP are
not mandatory dependencies.

The Ubuntu headless plotting setup uses `gnuplot-nox`, `fonts-freefont-otf`,
`fonts-dejavu-core` and `ghostscript` with Octave. Missing FreeSans fonts and a
missing `gs` command prevented PNG rendering in a minimal installation;
mathematical operations were separately functional. The interface version floor
is distinct from the exact runtime versions tested for this release.

GNU Octave package discovery reports what the selected installation registers.
Calling `run_script(..., packages=(... ,))` loads named installed packages for
that process. Octave Courier does not download, install or upgrade packages.

The source distribution declares build requirements in `pyproject.toml`. A clean
build may need access to a package index; offline users must make the build
requirements available themselves. Installing the release wheel avoids rebuilding
the package.

See [release notes](RELEASE-NOTES.md) for actual tested Python/Octave versions,
and [third-party notices](THIRD-PARTY-NOTICES.md) for licensing distinctions.
