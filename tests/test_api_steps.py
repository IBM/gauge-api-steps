#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import contextlib
import inspect
import io
import os
import unittest

from getgauge.python import data_store
from pathlib import Path
from unittest.mock import Mock

from gauge_api_steps.api_steps import (
    opener_key, body_key, response_key,
    add_body, append_to_file, beforescenario, pretty_print, simulate_response
)


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

    def test_add_body(self):
        body = "body"
        add_body(body)
        self.assertEqual(body, data_store.scenario[body_key])

    def test_simulate_response(self):
        resp = '{"a": "b"}'
        simulate_response(resp)
        self.assertEqual(data_store.scenario[response_key]["body"], resp.encode("UTF-8"))

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

    def test_pretty_print(self):
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            pretty_print('{"a":1,"b":2}')
            pretty = buf.getvalue()
            self.assertEqual('{\n    "a": 1,\n    "b": 2\n}\n', pretty)
