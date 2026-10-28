# Install on Linux

The Linux x86_64 distribution is a portable Python launcher and package. It
requires Python 3.10 or later and a separately installed GNU Octave. It does not
require PowerShell and is not advertised as a frozen standalone executable.

Install GNU Octave using your distribution's supported packages or the
[official GNU Octave guidance](https://octave.org/download). For Debian/Ubuntu,
the usual packages are:

```sh
sudo apt-get update
sudo apt-get install octave gnuplot-nox fonts-freefont-otf fonts-dejavu-core ghostscript
```

The font packages supply fonts used by the tested Octave plotting
configuration. Missing fonts can prevent PNG rendering even when calculations
and gnuplot execute successfully. Ghostscript supplies `gs`, which Octave's PNG
printing path uses. Package names and available versions depend on your distribution. These are
operator-run installation commands, not actions performed automatically by
Octave Courier.

## Launcher archive

Download `octave-courier-v0.1.0-linux-x86_64.tar.gz` and the release
`SHA256SUMS` from [v0.1.0](https://github.com/chatgptopenaiagi/octave-courier/releases/tag/v0.1.0).
Verify the checksum before extracting:

```sh
sha256sum octave-courier-v0.1.0-linux-x86_64.tar.gz
tar -xzf octave-courier-v0.1.0-linux-x86_64.tar.gz
cd octave-courier-v0.1.0-linux-x86_64
```

Run the archive's `bin/octave-courier` launcher from the extracted directory:

```sh
./bin/octave-courier discover
./bin/octave-courier --octave /usr/bin/octave-cli matrix --a '[[1,2],[3,4]]' --b '[[5,6],[7,8]]'
./bin/octave-courier plot --output sine.png
```

Keep the launcher together with its adjacent package files. The launcher discovers
its files relative to its own location, not the working directory.

## Python wheel

Download `octave_courier-0.1.0-py3-none-any.whl`, then:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install ./octave_courier-0.1.0-py3-none-any.whl
.venv/bin/octave-courier discover
.venv/bin/octave-courier doctor
```

Some Linux distributions package `venv` separately. The source distribution
can also be installed with `python3 -m pip install ./octave_courier-0.1.0.tar.gz`;
its build tools must be available as described in [Dependencies](DEPENDENCIES.md).

Linux x86_64 verification is recorded in [release notes](RELEASE-NOTES.md).
ARM64 and macOS are unverified for this release. A platform-independent wheel
does not imply that those targets were executed successfully.
