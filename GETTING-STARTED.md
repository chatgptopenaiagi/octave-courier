# Getting started

1. Install GNU Octave separately from [octave.org](https://octave.org/download).
2. Choose the Windows executable, Linux launcher archive or Python wheel from
   [v0.1.0](https://github.com/chatgptopenaiagi/octave-courier/releases/tag/v0.1.0).
3. Follow the [Windows](INSTALL-WINDOWS.md) or [Linux](INSTALL-LINUX.md) instructions.

Check discovery before doing a calculation:

```console
octave-courier discover
octave-courier packages
octave-courier matrix --a "[[1,2],[3,4]]" --b "[[5,6],[7,8]]"
octave-courier solve --a "[[3,1],[1,2]]" --b "[[9],[8]]"
octave-courier compute statistics --values "[[1,2,3,4]]"
octave-courier plot --output sine.png
```

The matrix product is `[[19,22],[43,50]]`. The linear-system solution is
`[[2],[3]]`; its residual can be independently checked in
[the Python example](examples/python_api.py).

`doctor` runs the built-in representative checks, including a PNG export:

```console
octave-courier doctor
```

If Octave is not found, pass its executable with the global `--octave` option
before the command, or set `OCTAVE_EXECUTABLE`. The explicit path selects your
installed program; it is not copied into Octave Courier.

```console
octave-courier --octave /usr/bin/octave-cli --timeout 30 doctor
```

Use a new output filename for plots. Keep the JSON result and its numerical
assumptions with your research. A successful process exit does not prove that
an arbitrary script meets its mathematical requirements.

The [examples](MATHEMATICAL-EXAMPLES.md) cover calculations, plotting, Python use
and expected failures. [Known limitations](KNOWN-LIMITATIONS.md) explain the
supported data contract and the distinction between intended and tested versions.
