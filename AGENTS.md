# Octave Courier engineering

Keep the product independent of workstation paths and other projects. Core API
and CLI use Python's standard library and a separately installed GNU Octave.
Treat requested script execution as trusted local code, never a sandbox.

Run unit tests before packaging. Integration tests require a real Octave runtime;
record actual tested Python, Octave, OS and architecture separately from intended
compatibility. Do not claim untested packages or platforms work.

Keep private build logs, machine paths, credentials and preservation receipts in
the ignored `.release/` directory. Stage an explicit public file list. Never copy
private project contents or original environments into this repository.

Release assets live under ignored `dist/`. A release manifest must bind the final
source commit, artifact sizes/hashes and clean-install verification. Preserve
the operator's existing CLI executable/configuration and original source project.
