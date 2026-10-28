# Known limitations

- **Octave is external.** A functioning Octave installation is required. The
  Windows executable includes Python, not GNU Octave.
- **The numeric JSON contract is deliberately small.** Inputs and outputs are
  finite real doubles with explicit two-dimensional shape. Complex, sparse,
  symbolic, arbitrary-precision and user-defined Octave objects are not exchanged
  losslessly. Integer inputs outside `[-2**53, 2**53]` are rejected; floating-point
  inputs and results still have normal double-precision rounding.
- **Matrices are bounded.** Input dimensions are 1–256 rows and columns. This
  initial interface is not an unbounded batch-computing service.
- **A solve is not a proof of a model.** Check residuals, conditioning, tolerances
  and problem assumptions for your data.
- **Scripts are trusted code.** They run with the current user's permissions.
  Startup isolation and argument handling are not a sandbox.
- **Calls are independent.** Every operation starts a new Octave process. There
  is no persistent workspace, shared variable session or arbitrary expression API.
- **Plotting has system dependencies.** The gnuplot backend and its printing/font
  tools must work. PNG export does not verify an interactive GUI.
- **Package discovery is not certification.** The original environment
  catalogued 55 packages; only selected functions were exercised there. v0.1.0's
  core demonstrations do not claim support for every package or combination.
- **Platform testing is scoped.** See the exact combinations in
  [release notes](RELEASE-NOTES.md). ARM64, macOS and arbitrary Linux distributions
  are not verified merely because a wheel has a platform-independent tag.
- **No optional service integration is advertised.** v0.1.0 has no MCP server,
  database adapter, spreadsheet integration or Nacre-11 integration.
- **Runtime changes need new tests.** Package or executable changes after a
  successful release test are not continuously monitored by this library.
