# Third-party notices

## GNU Octave

GNU Octave performs the mathematical calculations and is installed separately.
Octave Courier does not include or modify the GNU Octave distribution. GNU Octave
is copyright its respective contributors and is licensed under GPL version 3 or
later. Consult its installed `COPYING` file and the
[GNU Octave copyright information](https://octave.org/copyright/).

The name GNU Octave identifies that external software. Octave Courier is an
independent project and does not claim GNU Octave authorship or endorsement.

## Python runtime

The wheel and Linux launcher use the user's external Python installation. The
Windows executable includes a Python runtime. Python retains its applicable
Python Software Foundation and incorporated-software licenses. Distribution
archives include runtime license notices collected from the actual build
environment; those notices are not replaced by the Octave Courier MIT license.
See [Python's licensing documentation](https://docs.python.org/3/license.html).

## PyInstaller

PyInstaller is used to build the Windows executable. Its licensing includes an
exception permitting generated application bundles to use the application's
license, subject to dependency licenses. PyInstaller is not a required package
for users of the wheel or Linux launcher. See the
[PyInstaller license](https://pyinstaller.org/en/stable/license.html) and any
build-tool notice included with the release distribution.

## Optional libraries

NumPy and other scientific Python libraries are not bundled by the core wheel
and are not mandatory dependencies. When installed independently, they retain
their own licenses. No optional database, spreadsheet, model runtime or MCP
implementation is included in v0.1.0.
