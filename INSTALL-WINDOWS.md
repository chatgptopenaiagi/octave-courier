# Install on Windows

The release provides a Windows x86_64 executable for Windows 11 x64. GNU Octave
must be installed separately. The executable contains its Python runtime, so
Python is not required for this option.

## Executable distribution

Download `octave-courier-v0.1.0-windows-x86_64.exe` from
[the release](https://github.com/chatgptopenaiagi/octave-courier/releases/tag/v0.1.0).
The accompanying ZIP includes the executable and distribution notices. Compare
your download against the release `SHA256SUMS` file:

```powershell
Get-FileHash -LiteralPath '.\octave-courier-v0.1.0-windows-x86_64.exe' -Algorithm SHA256
& '.\octave-courier-v0.1.0-windows-x86_64.exe' discover
& '.\octave-courier-v0.1.0-windows-x86_64.exe' matrix --a '[[1,2],[3,4]]' --b '[[5,6],[7,8]]'
& '.\octave-courier-v0.1.0-windows-x86_64.exe' plot --output '.\sine.png'
```

Standard GNU Octave installations under Program Files are searched automatically.
An explicit path is also supported; use the path installed on your computer:

```powershell
& '.\octave-courier-v0.1.0-windows-x86_64.exe' `
  --octave 'C:\Program Files\GNU Octave\Octave-11.3.0\mingw64\bin\octave-cli.exe' doctor
```

The executable is an initial community release, not a signed installer. Extract
ZIP downloads into a writable directory. It can run from a directory unrelated
to the source checkout.

## Python wheel

With Python 3.10 or later installed, download
`octave_courier-0.1.0-py3-none-any.whl`, then use an isolated environment:

```powershell
py -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install '.\octave_courier-0.1.0-py3-none-any.whl'
& '.\.venv\Scripts\octave-courier.exe' doctor
& '.\.venv\Scripts\python.exe' '.\examples\python_api.py'
```

The last command assumes you also downloaded the examples archive. The wheel
does not require NumPy, SciPy, PowerShell modules or an MCP server. GNU Octave
and its gnuplot graphics backend are still required for their operations.

Install the source distribution similarly with
`python -m pip install ./octave_courier-0.1.0.tar.gz`. Building the source
distribution requires the build dependencies in `pyproject.toml`; it may need
network access unless those dependencies are already available.

See [release notes](RELEASE-NOTES.md) for the actual clean-install test versions
and [CLI reference](CLI-REFERENCE.md) for exit and timeout behavior.
