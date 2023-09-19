import inspect
import os
import unittest

from getgauge.python import data_store
from pathlib import Path
from unittest.mock import Mock

from gauge_api_steps.api_steps import opener_key, append_to_file, beforescenario


class TestApiSteps(unittest.TestCase):

    def setUp(self):
        data_store.scenario.clear()
        self.app_context = Mock()
        self.test_dir = str(Path(inspect.getfile(self.__class__)).parent.absolute())
        self.out = os.path.join(self.test_dir, "out")
        if not os.path.exists(self.out):
            os.mkdir(self.out)

    def test_beforescenario(self):
        beforescenario(self.app_context)
        self.assertIsNotNone(data_store.scenario[opener_key])

    def test_append(self):
        os.environ["GAUGE_PROJECT_ROOT"] = self.test_dir
        out_file = f"{self.out}/output.csv"
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
