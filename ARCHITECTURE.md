# Architecture

Octave Courier has three small layers:

1. **Discovery** resolves an explicit executable or an installed Octave runtime.
2. **Python API and CLI** validate inputs, start a bounded child and interpret results.
3. **An included Octave worker** performs implemented operations and writes a
   structured response.

GNU Octave is an external executable. No Octave interpreter, package collection,
database server, agent framework or model runtime is included in the core package.

For fixed calculations, the caller writes a JSON request into a new temporary
directory. The child reads it, computes with Octave and writes a JSON response.
The response separates flat numeric values from shape metadata. The Python side
checks the schema, operation, dimensions and finite numeric values before
returning a result. The data channel does not accept arbitrary Octave expressions.

Script execution is a separate, explicit operation. A caller-selected `.m` file
receives a real argument vector. Requested installed packages load only in the
child, and site/user startup files and command history are disabled. A script can
still use the current account's permissions; this is a process boundary, not a
security sandbox.

Children have time limits. The API returns structured process information or
raises typed failures. Each calculation starts a fresh process, so mutable Octave
workspace state is not shared between unrelated calls.

The Windows executable freezes the Python side and worker resource. It still
discovers and starts a separately installed Octave. The Linux archive supplies a
Python launcher and the same package; it requires an external Python interpreter.
The wheel is pure Python with the worker included as package data.

The ordinary API and CLI work without Codex. v0.1.0 does not implement an MCP
server; MCP remains an optional future interface rather than a base dependency.
