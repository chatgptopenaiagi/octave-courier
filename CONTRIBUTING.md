# Contributing

Please open an [issue](https://github.com/chatgptopenaiagi/octave-courier/issues)
with a reproducible case before proposing a broad interface change. Include
Octave Courier, Python and GNU Octave versions, your operating system and the
smallest input that demonstrates the problem. Remove private paths, credentials
and research data you cannot publish.

For a development checkout, create and activate a virtual environment using your
platform's standard procedure, then install the checkout and run the tests:

```console
python -m venv .venv
python -m pip install -e .
python -m unittest discover -s tests -v
```

Use the virtual environment's Python command for installation and tests.
Integration tests require a real GNU Octave executable. Set `OCTAVE_EXECUTABLE`
when it is not discoverable. Tests should distinguish skipped runtime-dependent
checks from successful mathematical execution.

Changes should preserve shape, numerical/error contracts, Unicode arguments,
resource cleanup and cross-platform paths. Add tests that exercise observable
behavior, including failures where they matter. Keep optional scientific or
service dependencies out of the base package.

Use synthetic examples with an independent expected answer or residual check.
Do not infer compatibility for all packages from a small passing subset. Report
which runtime and platform you actually tested.

Contributions are provided under the project's [MIT license](LICENSE). Preserve
applicable third-party notices when adding or adapting material.
