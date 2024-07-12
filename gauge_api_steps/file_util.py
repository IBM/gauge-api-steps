#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import os

def assert_file_is_in_project(file_name: str) -> str:
    file_path = os.path.realpath(file_name)
    project_root = os.path.realpath(os.environ.get("GAUGE_PROJECT_ROOT"))
    if not file_path.startswith(project_root):
        raise AssertionError(f"file must be inside {project_root}, but found in {file_path}")
    return file_path
