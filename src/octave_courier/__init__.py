"""Octave Courier: a small independent GNU Octave integration interface."""
from .discovery import OctaveError, OctaveNotFound, discover
from .engine import Octave, OctaveExecutionError, OctaveTimeoutError, ValidationError

__version__ = "0.1.0"
__all__ = ["Octave", "discover", "OctaveError", "OctaveNotFound", "OctaveExecutionError", "OctaveTimeoutError", "ValidationError", "__version__"]
