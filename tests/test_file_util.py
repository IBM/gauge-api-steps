#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import os
import unittest

from gauge_api_steps.file_util import assert_file_is_in_project
from tests import TEST_DIR, TEST_RESOURCES_DIR


class TestFileUtil(unittest.TestCase):

    def setUp(self):
        os.environ["GAUGE_PROJECT_ROOT"] = TEST_DIR

    def test_assert_file_is_in_project(self):
        result = assert_file_is_in_project(f"{TEST_RESOURCES_DIR}/file.txt")
        self.assertIsNotNone(result)

    def test_assert_file_is_in_project_fails(self):
        self.assertRaises(AssertionError, lambda: assert_file_is_in_project("/root/file.txt"))
