import os
import unittest

from getgauge.python import data_store
from unittest.mock import Mock

from gauge_api_steps.api_steps import opener_key, append_to_file, beforescenario


class TestApiSteps(unittest.TestCase):

    def setUp(self):
        data_store.scenario.clear()
        self.app_context = Mock()

    def test_beforescenario(self):
        beforescenario(self.app_context)
        self.assertIsNotNone(data_store.scenario[opener_key])

    def test_append(self):
        os.environ["GAUGE_PROJECT_ROOT"] = "./tests/out"
        out_file = "tests/out/output.csv"
        if os.path.isfile(out_file):
            os.remove(out_file)
        append_to_file(out_file, "a,b,c")
        append_to_file(out_file, "aa,bb,cc")
        with open(out_file) as f:
            contents = f.read()
        self.assertEqual("a,b,c\naa,bb,cc\n", contents, f"got unexpected content in output file {out_file}")

    def test_append_fails(self):
        os.environ["GAUGE_PROJECT_ROOT"] = "./tests/out"
        out_file = "tests/notvalid/output.csv"
        self.assertRaises(AssertionError, lambda: append_to_file(out_file, "a,b,c"))
