# Security policy

Octave Courier executes a local GNU Octave process. The `run` command and
`run_script` API execute scripts with the current account's permissions. They
are intended for trusted local code and are not an isolation service for hostile
input. A timeout limits process duration, not filesystem or network access.

Fixed matrix and demonstration operations accept structured data and implemented
operation names. They do not evaluate arbitrary expressions from JSON. Keep
Octave and your operating system's dependencies maintained through their own
supported update mechanisms.

Do not run an executable selected by an untrusted `OCTAVE_EXECUTABLE` value or
an untrusted `PATH`. Download releases from this repository and check the
published SHA-256 manifest.

Report a suspected vulnerability through GitHub's private vulnerability reporting
feature if it is available for the repository. If that feature is unavailable,
open an issue requesting a private reporting route without publishing exploit
details, credentials or sensitive files. The project has no guaranteed response
time or long-term support commitment for this initial release.
