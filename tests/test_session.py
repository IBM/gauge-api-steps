#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import os
import unittest

from getgauge.python import data_store
from unittest.mock import call, mock_open, patch
from tests import TEST_DIR, TEST_RESOURCES_DIR
from gauge_api_steps.session import (
    session_changed_key, session_file_key, session_keys_key,
    load_session_properties, save_session_properties, store_in_session, session_properties
)


class TestSession(unittest.TestCase):

    def setUp(self):
        data_store.scenario.clear()
        os.environ["GAUGE_PROJECT_ROOT"] = TEST_DIR

    def test_load_session_properties(self):
        props_file = f"{TEST_DIR}/session.properties"
        os.environ["session_properties"] = props_file
        data = ('a = 1\n'
            'b = \n'
            'c = {\\n  \\"key\": \\"value\\",\\n  \\"else\\": \\"\\\\0x41\"\\n}\n')
        with patch("builtins.open", mock_open(read_data=data)) as mocked_open, patch("os.path.exists") as mocked_exists:
            mocked_exists.return_value = True
            load_session_properties(props_file)
        mocked_open.assert_called_with(props_file)
        self.assertTrue("/session.properties" in data_store.scenario[session_file_key])
        self.assertEqual("1", data_store.scenario["a"])
        self.assertEqual("", data_store.scenario["b"])
        self.assertEqual('{\n  "key": "value",\n  "else": "\\0x41"\n}', data_store.scenario["c"])

    def test_save_session_properties_does_nothing(self):
        data_store.scenario[session_changed_key] = False
        with patch("builtins.open") as mocked_open:
            save_session_properties()
        mocked_open.assert_not_called()

    def test_save_session_properties_does_something(self):
        data_store.scenario[session_changed_key] = True
        props_file = f"{TEST_RESOURCES_DIR}/session.properties"
        data_store.scenario[session_file_key] = props_file
        data_store.scenario[session_keys_key] = ['a', 'b', 'c']
        data_store.scenario['a'] = '1'
        data_store.scenario['b'] = ''
        data_store.scenario['c'] = '{\n  "key": "value",\n  "else": "\\0x41"\n}'
        with patch("builtins.open", mock_open()) as mocked_open, patch("os.replace") as mocked_replace:
            save_session_properties()
        mocked_open.assert_called_with(f"{props_file}.tmp", 'w')
        handle = mocked_open()
        handle.write.assert_has_calls([
            call('a = 1\n'),
            call('b = \n'),
            call('c = {\\n  "key": "value",\\n  "else": "\\\\0x41"\\n}\n')
        ])
        mocked_replace.assert_called_with(f"{props_file}.tmp", props_file)

    def test_store_in_session(self):
        store_in_session("foo", "bar")
        self.assertEqual("bar", data_store.scenario["foo"])
        self.assertTrue(data_store.scenario[session_changed_key])
        self.assertTrue("foo" in data_store.scenario[session_keys_key])

    def test_session_properties(self):
        os.environ.setdefault("should_not", "be_included")
        data_store.scenario["should_not"] = "be_included"
        store_in_session("key", "value")
        result = session_properties()
        self.assertEqual({"key": "value"}, result)
