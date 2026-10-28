"""Hermetic executable precedence/discovery checks without installing Octave."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from octave_courier import OctaveNotFound, discover


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.fake = self.folder / "octave fake"
        self.fake.write_text("placeholder discovery fixture", encoding="utf-8")
        self.fake.chmod(0o755)

    def test_explicit_existing_path_precedes_environment(self):
        with patch.dict(os.environ, {"OCTAVE_EXECUTABLE": str(self.folder / "missing")}):
            self.assertEqual(discover(self.fake), self.fake.resolve())

    def test_missing_explicit_path_never_silently_falls_back(self):
        with self.assertRaises(OctaveNotFound):
            discover(self.folder / "missing")

    def test_environment_override_is_authoritative(self):
        with patch.dict(os.environ, {"OCTAVE_EXECUTABLE": str(self.fake)}):
            self.assertEqual(discover(), self.fake.resolve())
        with patch.dict(os.environ, {"OCTAVE_EXECUTABLE": str(self.folder / "missing")}):
            with self.assertRaises(OctaveNotFound):
                discover()

    def test_path_executable_name_can_be_explicit(self):
        with patch("octave_courier.discovery.shutil.which", return_value=str(self.fake)):
            self.assertEqual(discover("octave-cli"), self.fake.resolve())

    def test_directory_is_not_executable(self):
        with patch("octave_courier.discovery.shutil.which", return_value=None):
            with self.assertRaises(OctaveNotFound):
                discover(self.folder)

    def test_no_available_runtime_has_useful_error(self):
        with patch.dict(os.environ, {"OCTAVE_EXECUTABLE": "", "ProgramFiles": "", "ProgramW6432": "", "ProgramFiles(x86)": ""}), patch("octave_courier.discovery.shutil.which", return_value=None):
            with self.assertRaisesRegex(OctaveNotFound, "Install it separately"):
                discover()

    def test_automatic_lookup_does_not_implicitly_trust_current_directory(self):
        previous = Path.cwd()
        local = self.folder / "octave-cli"
        local.write_text("untrusted same-name current-directory fixture",encoding="utf-8")
        local.chmod(0o755)
        os.chdir(self.folder)
        try:
            with patch.dict(os.environ, {"OCTAVE_EXECUTABLE": "", "ProgramFiles": "", "ProgramW6432": "", "ProgramFiles(x86)": ""}), patch("octave_courier.discovery.shutil.which", return_value=None):
                with self.assertRaises(OctaveNotFound):
                    discover()
        finally:
            os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
