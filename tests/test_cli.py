"""Public CLI behavior: machine-readable output and actionable failure exits."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch

from octave_courier import cli


class CliTests(unittest.TestCase):
    def call(self, arguments):
        out, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(error):
            code = cli.main(arguments)
        return code, out.getvalue(), error.getvalue()

    def test_matrix_json_and_explicit_runtime(self):
        with patch.object(cli, "Octave") as runtime:
            runtime.return_value.matrix_product.return_value = {"shape": [1, 1], "result": [[6]]}
            code, out, error = self.call(["--octave", "/explicit/octave", "matrix", "--a", "[[2]]", "--b", "[[3]]"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["result"], [[6]])
        self.assertFalse(error)
        runtime.assert_called_once_with(executable="/explicit/octave", timeout=30)

    def test_invalid_numeric_input_is_structured_error(self):
        with patch.object(cli, "Octave") as runtime:
            runtime.return_value.matrix_product.side_effect = ValueError("Expected a rectangular finite real matrix")
            code, out, error = self.call(["matrix", "--a", "[[1],[2,3]]", "--b", "[[1]]"])
        self.assertEqual(code, 1)
        self.assertFalse(out)
        self.assertEqual(json.loads(error)["error"]["type"], "ValueError")

    def test_script_arguments_are_preserved(self):
        arguments = ["space argument", "quote'\"", "Ω漢字", "$(literal); & data"]
        with patch.object(cli, "Octave") as runtime:
            runtime.return_value.run_script.return_value = {"exit_code": 0, "stdout": "ok"}
            code, _, _ = self.call(["run", "script.m", "--", *arguments])
        self.assertEqual(code, 0)
        self.assertEqual(runtime.return_value.run_script.call_args.kwargs["args"], arguments)

    def test_statistics_option_rejected_for_other_operations(self):
        with patch.object(cli, "Octave"):
            code, out, error = self.call(["compute", "signal", "--values", "[1,2]"])
        self.assertEqual(code, 1)
        self.assertFalse(out)
        self.assertIn("statistics", json.loads(error)["error"]["message"])


if __name__ == "__main__":
    unittest.main()
