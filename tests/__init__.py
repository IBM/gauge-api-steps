#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

from pathlib import Path

_test_dir = Path(__file__).absolute().parent
TEST_DIR = str(_test_dir)
PROJECT_DIR = str(_test_dir.parent)
TEST_RESOURCES_DIR = str(_test_dir.joinpath("resources"))
TEST_OUT_DIR = str(_test_dir.joinpath("out"))
