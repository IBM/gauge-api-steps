#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import inspect
import os
import unittest

from pathlib import Path
from gauge_api_steps.file_util import assert_file_is_in_project


class TestFileUtil(unittest.TestCase):

    def setUp(self):
        path = Path(inspect.getfile(self.__class__))
        test_dir = path.parent.absolute()
        self.resources = str(os.path.join(test_dir, "resources"))
        os.environ["GAUGE_PROJECT_ROOT"] = str(test_dir)

    def test_assert_file_is_in_project(self):
        result = assert_file_is_in_project(f"{self.resources}/file.txt")
        self.assertIsNotNone(result)

    def test_assert_file_is_in_project_fails(self):
        self.assertRaises(AssertionError, lambda: assert_file_is_in_project("/root/file.txt"))
