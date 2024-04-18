#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import inspect
import os
import re
import time
import unittest

from datetime import datetime
from getgauge.python import data_store
from pathlib import Path

from gauge_api_steps.substitute import substitute


class TestSubstitute(unittest.TestCase):

    def setUp(self):
        self.startTime = time.time()
        path = Path(inspect.getfile(self.__class__))
        test_dir = path.parent.absolute()
        self.resources = str(os.path.join(test_dir, "resources"))
        os.environ["GAUGE_PROJECT_ROOT"] = str(test_dir)

    def tearDown(self):
        t = time.time() - self.startTime
        print(f"{t:.3f}s")

    def test_substitute_replace(self):
        tableflip = "(ノಠ益ಠ)ノ彡┻━┻"
        os.environ["placeholder"] = tableflip
        result = substitute("${placeholder}")
        self.assertEqual(tableflip, result)

    def test_substitute_with_full_math_expression(self):
        result = substitute("#{1 + 1}")
        self.assertEqual("2", result)

    def test_substitute_with_inner_math_expression(self):
        result = substitute("\(^#{0 + 0}^)/")
        self.assertEqual("\(^0^)/", result)

    def test_substitute_with_two_math_expressions(self):
        result = substitute("#{0 + 0}#{1 + 1}")
        self.assertEqual("02", result)

    def test_substitute_complex(self):
        os.environ["a"] = "1"
        result = substitute("(${a} + 1) ** 2 = #{($a + 1) ** 2}")
        self.assertEqual("(1 + 1) ** 2 = 4", result)

    def test_substitute_fails(self):
        result = substitute("}#{1 + 1")
        self.assertEqual("}#{1 + 1", result)

    def test_substitute_with_bracket_diversions(self):
        result = substitute("}#{0 + 0}#{")
        self.assertEqual("}0#{", result)

    def test_substitute_without_pipe_operator(self):
        placeholder1 = "lala"
        placeholder2 = "baba"
        os.environ["placeholder1"] = placeholder1
        data_store.scenario["placeholder2"] = placeholder2
        result = substitute("This is ${placeholder1}/url and ${placeholder2}")
        self.assertEqual("This is lala/url and baba", result)

    def test_substitute_with_uuid_expression(self):
        result = substitute("!{uuid}")
        self.assertRegex(result, "^[0-9a-f]{8}.[0-9a-f]{4}.[0-9a-f]{4}.[0-9a-f]{4}.[0-9a-f]{12}$")

    def test_substitute_with_time_expression(self):
        result = substitute("!{time}")
        self.assertTrue(self._datetime_valid(result))

    def test_substitute_with_time_and_format_expression(self):
        result = substitute("!{time:%Y}")
        self.assertTrue(re.fullmatch("[0-9]{4}", result) is not None)

    def test_substitute_raises_with_invalid_time(self):
        self.assertRaises(ValueError, lambda: substitute("!{time-ly}"))

    def test_substitute_raises_with_invalid_expression(self):
        self.assertRaises(ValueError, lambda: substitute("!{nonexistent}"))

    def test_substitute_with_file(self):
        test_file = f"{self.resources}/file.txt"
        param = "!{file:{test_file}}".replace("{test_file}", test_file)
        result = substitute(param)
        self.assertEqual("Test file\n", result)

    def test_substitute_with_file_outside_project(self):
        self.assertRaises(AssertionError, lambda: substitute("!{file:/root/file.txt}"))

    def test_substitute_with_gql(self):
        test_file = f"{self.resources}/file.gql"
        param = "!{gql:{test_file}}".replace("{test_file}", test_file)
        result = substitute(param)
        self.assertEqual('{"query": "query ExampleQuery {\\n  find {\\n    me\\n  }\\n}\\n"}', result)

    def test_substitute_with_gql_outside_project(self):
        self.assertRaises(AssertionError, lambda: substitute("!{gql:/root/file.gql}"))

    def _datetime_valid(self, dt_str: str) -> bool:
        try:
            datetime.fromisoformat(dt_str)
        except ValueError:
            return False
        return True


if __name__ == '__main__':
    unittest.main()
