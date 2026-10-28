"""Independent numerical checks and real process-boundary verification."""
import json
import math
import os
from pathlib import Path
import struct
import tempfile
import unittest

from octave_courier import Octave, OctaveExecutionError, OctaveNotFound, OctaveTimeoutError, ValidationError
from octave_courier.engine import _matrix, _timeout


class InputTests(unittest.TestCase):
    def test_reject_nonfinite_complex_boolean_ragged_and_unrepresentable_int(self):
        invalid = [[], [[1], [1, 2]], [[True]], [[float("nan")]], [[float("inf")]], [[1j]], [[2**53+1]], [["1"]], [1, 2], [[1]*257]]
        for value in invalid:
            with self.subTest(value=str(value)[:60]), self.assertRaises(ValidationError):
                _matrix(value, "a")

    def test_double_boundary_and_shape_are_explicit(self):
        result = _matrix([[2**53, 0.5], [-2**53, -2.5]], "a")
        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["columns"], 2)
        self.assertEqual(result["values"], [float(2**53), .5, -float(2**53), -2.5])

    def test_timeout_values_are_bounded(self):
        for value in [True, 0, -1, float("nan"), float("inf"), 3601, "1"]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                _timeout(value)


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.octave = Octave(timeout=40)
        except OctaveNotFound as error:
            raise unittest.SkipTest(str(error))

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="courier test's Ω ")
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)

    def script(self, text):
        path = self.folder / "script's Ω.m"
        path.write_text(text, encoding="utf-8")
        return path

    def test_version_and_info(self):
        self.assertGreaterEqual(int(self.octave.runtime_version.split('.')[0]), 7)
        self.assertEqual(self.octave.info()["octave_version"], self.octave.runtime_version)

    def test_required_matrix_product(self):
        answer = self.octave.matrix_product([[1, 2], [3, 4]], [[5, 6], [7, 8]])
        self.assertEqual(answer["result"], [[19, 22], [43, 50]])
        self.assertEqual(answer["shape"], [2, 2])

    def test_rectangular_and_singleton_shapes(self):
        for a, b, expected in [([[2]], [[3]], [[6]]), ([[1, 2]], [[3], [4]], [[11]]), ([[1], [2]], [[3, 4]], [[3, 4], [6, 8]])]:
            with self.subTest(a=a,b=b):
                self.assertEqual(self.octave.matrix_product(a,b)["result"], expected)

    def test_linear_solve_and_independent_residual(self):
        answer = self.octave.solve([[3, 1], [1, 2]], [[9, 2], [8, 3]])
        expected = [[2, .2], [3, 1.4]]
        for row, expected_row in zip(answer["result"], expected):
            for actual, value in zip(row, expected_row):
                self.assertAlmostEqual(actual, value, places=12)
        x = answer["result"]
        for a, b in [([3,1], [9,2]), ([1,2], [8,3])]:
            for column in range(2):
                self.assertLess(abs(sum(a[k]*x[k][column] for k in range(2))-b[column]),1e-12)
        self.assertLess(answer["residual_inf"], 1e-12)

    def test_bad_dimensions_are_rejected_before_execution(self):
        with self.assertRaises(ValidationError):
            self.octave.matrix_product([[1,2]], [[1,2]])
        with self.assertRaises(ValidationError):
            self.octave.solve([[1,2]], [[1]])

    def test_singular_and_overflow_fail(self):
        with self.assertRaises(OctaveExecutionError):
            self.octave.solve([[1,2],[2,4]], [[1],[2]])
        with self.assertRaises(OctaveExecutionError):
            self.octave.matrix_product([[1e308]], [[1e308]])

    def test_numerical_demonstration(self):
        result = self.octave.compute("numerical")["result"]
        self.assertAlmostEqual(result["integral_x2_0_1"],1/3,places=12)
        self.assertAlmostEqual(result["integral_sin_0_pi"],2,places=10)
        self.assertAlmostEqual(result["sqrt2_root"],math.sqrt(2),places=10)
        self.assertAlmostEqual(result["decay_at_one"],math.exp(-1),places=7)

    def test_statistics_sample_normalization(self):
        result = self.octave.compute("statistics")["result"]
        self.assertEqual(result["count"],5)
        self.assertEqual(result["mean"],3)
        self.assertEqual(result["median"],3)
        self.assertEqual(result["sample_variance"],2.5)
        self.assertAlmostEqual(result["sample_std"],math.sqrt(2.5),places=12)
        with self.assertRaises(ValidationError):
            self.octave.compute("statistics",values=[[1]])

    def test_statistics_overflow_is_not_silently_json_null(self):
        with self.assertRaises(OctaveExecutionError):
            self.octave.compute("statistics",values=[[1e308,-1e308]])

    def test_signal_demonstration(self):
        result = self.octave.compute("signal")["result"]
        self.assertEqual(result["fft_real"],[1,1,1,1])
        self.assertEqual(result["fft_imag"],[0,0,0,0])
        self.assertEqual(result["convolution"],[1,3,2])
        self.assertEqual(result["fir_filter"],[.5,1,1,1])

    def test_optimization_demonstration(self):
        result = self.octave.compute("optimization")["result"]
        self.assertAlmostEqual(result["location"],3,places=6)
        self.assertAlmostEqual(result["objective"],7,places=10)

    def test_unknown_expression_and_parameters_are_rejected(self):
        for name, parameters in [("eval",{}),([] ,{}),("numerical",{"expression":"exit()"}),("statistics",{"function":"eval"})]:
            with self.subTest(name=name), self.assertRaises(ValidationError):
                self.octave.compute(name,**parameters)

    def test_package_catalog_is_discovery_only(self):
        result = self.octave.packages()
        self.assertIsInstance(result["packages"],list)
        self.assertEqual(result["count"],len(result["packages"]))
        self.assertIn("registrations only",result["scope"])

    def test_script_literal_unicode_arguments_and_startup_isolation(self):
        (self.folder/".octaverc").write_text('error("must not load startup");',encoding="utf-8")
        args=["space argument","quote'and\"double","Ω漢字","$(no_command); & data","line1\nline2"]
        result=self.octave.run_script(self.script('printf("%s",jsonencode(argv()));'),args=args)
        self.assertEqual(json.loads(result["stdout"]),args)
        self.assertEqual(result["exit_code"],0)

    def test_nonzero_script_exit_is_carried(self):
        with self.assertRaises(OctaveExecutionError) as context:
            self.octave.run_script(self.script('fprintf(stderr,"expected failure"); exit(7);'))
        self.assertEqual(context.exception.result["exit_code"],7)
        self.assertIn("expected failure",context.exception.result["stderr"])

    def test_script_timeout_terminates_child(self):
        with self.assertRaises(OctaveTimeoutError) as context:
            self.octave.run_script(self.script('pause(20);'),timeout=.5)
        self.assertTrue(context.exception.result["timed_out"])
        self.assertLess(context.exception.result["elapsed_ms"],8000)

    def test_script_package_names_are_data(self):
        with self.assertRaises(ValidationError):
            self.octave.run_script(self.script('disp(1);'),packages=["signal');exit();%"])

    def test_plot_produces_png_and_preserves_existing_output(self):
        path=self.folder/"sine's Ω.png"
        result=self.octave.plot(path)
        self.assertEqual(result["output"],str(path.resolve()))
        self.assertEqual(path.read_bytes()[:8],b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II",path.read_bytes()[16:24]),(result["width"],result["height"]))
        self.assertGreater(result["bytes"],1000)
        with self.assertRaises(ValidationError):self.octave.plot(path)


if __name__ == "__main__":
    unittest.main()
