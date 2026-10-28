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

The frozen runtime also incorporates libmpdec 4.0.0 (copyright 2008–2024 Stefan
Krah, BSD two-clause terms) and Unicode 16.0 data (Unicode, Inc., Unicode License
V3). Their complete notices are preserved in
[libmpdec's license](build_tools/licenses/libmpdec-4.0.0-LICENSE.txt) and
[the Unicode license](build_tools/licenses/Unicode-LICENSE.txt), embedded license
data and the ZIP's `licenses` directory. The collected Python license also
retains its incorporated bzip2, libffi and Zstandard notices.

The Windows executable includes unmodified Microsoft Visual C++ runtime
components, version 14.51.36247.0. These retain Microsoft's terms rather than
the project's MIT license. The collected Python license includes its additional
Windows binary-build distribution conditions; the separate
[Microsoft runtime terms](build_tools/licenses/Microsoft-VC14-Runtime-2026.txt)
are included as end-user terms, not described as a redistribution grant.
Windows 11 supplies its own Universal C Runtime and API-set system components;
those operating-system files are not bundled by this release.

## OpenSSL in the Windows executable

The Windows v0.1.0 frozen distribution includes OpenSSL 3.5.7 libraries
`libcrypto-3.dll` and `libssl-3.dll` through its embedded Python runtime.
OpenSSL is copyright the OpenSSL Project Authors and contributors and is
licensed under the Apache License, Version 2.0. These libraries were not modified
by Octave Courier.

The [upstream release license](build_tools/licenses/OpenSSL-3.5.7-LICENSE.txt)
is included in the public source, embedded executable license data and the ZIP's
`licenses` directory. The official [OpenSSL licensing information](https://openssl-library.org/source/license/)
also identifies Apache 2.0 for OpenSSL 3.x. The pure-Python wheel and Linux
launcher do not bundle these OpenSSL DLLs; their external Python installations
retain their own runtime components and licenses.

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
