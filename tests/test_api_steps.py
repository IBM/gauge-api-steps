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
from unittest.mock import Mock, call, mock_open, patch

from gauge_api_steps.api_steps import (
    opener_key, body_key, response_key, sent_request_headers_key, session_changed_key, session_file_key, session_keys_key,
    add_body, append_to_file, base64_decode, base64_encode, beforescenario, load_from_file, pretty_print, print_headers, print_status, print_body, save_file, simulate_response,
    _load_session_properties, _save_session_properties, _store_in_session
)


class TestApiSteps(unittest.TestCase):

    def setUp(self):
        data_store.scenario.clear()
        self.app_context = Mock()
        self.test_dir = str(Path(inspect.getfile(self.__class__)).parent.absolute())
        self.resources = os.path.join(self.test_dir, "resources")
        self.out = os.path.join(self.test_dir, "out")
        os.environ["GAUGE_PROJECT_ROOT"] = self.test_dir
        os.environ["session_properties"] = f"{self.test_dir}/session.properties"
        if not os.path.exists(self.out):
            os.mkdir(self.out)

    def test_beforescenario(self):
        beforescenario(self.app_context)
        self.assertIsNotNone(data_store.scenario[opener_key])

    def test_load_from_file(self):
        load_from_file(f"{self.resources}/file.txt", "testfile")
        self.assertEqual("Test file\n", data_store.scenario["testfile"])

    def test_add_body(self):
        body = "body"
        add_body(body)
        self.assertEqual(body, data_store.scenario[body_key])

    def test_simulate_response(self):
        resp = '{"a": "b"}'
        simulate_response(resp)
        self.assertEqual(data_store.scenario[response_key]["body"], resp.encode())

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

    def test_print_headers(self):
        data_store.scenario[sent_request_headers_key] = {'req': 'reqheader'}
        data_store.scenario.setdefault(response_key, {})["headers"] = [('resp', 'respheader')]
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            print_headers()
            result = buf.getvalue()
            self.assertEqual('Request headers:\n\n    req: reqheader\nResponse headers:\n\n    resp: respheader\n', result)

    def test_print_status(self):
        data_store.scenario.setdefault(response_key, {})["status"] = '200'
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            print_status()
            result = buf.getvalue()
            self.assertEqual('Response status:\n\n    200\n', result)

    def test_print_body(self):
        data_store.scenario.setdefault(response_key, {})["body"] = '{"a": "b", "c": 1}'.encode()
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            print_body()
            result = buf.getvalue()
            self.assertEqual('Response body:\n\n    {\n        "a": "b",\n        "c": 1\n    }\n', result)

    def test_load_session_properties(self):
        props_file = f"{self.test_dir}/session.properties"
        os.environ["session_properties"] = props_file
        data = ('a = 1\n'
            'b = \n'
            'c = {\\n  \\"key\": \\"value\\",\\n  \\"else\\": \\"\\\\0x41\"\\n}\n')
        with patch("builtins.open", mock_open(read_data=data)) as mocked_open, patch("os.path.exists") as mocked_exists:
            mocked_exists.return_value = True
            _load_session_properties()
        mocked_open.assert_called_with(props_file)
        self.assertTrue("/session.properties" in data_store.scenario[session_file_key])
        self.assertEqual("1", data_store.scenario["a"])
        self.assertEqual("", data_store.scenario["b"])
        self.assertEqual('{\n  "key": "value",\n  "else": "\\0x41"\n}', data_store.scenario["c"])

    def test_save_session_properties__does_nothing(self):
        data_store.scenario[session_changed_key] = False
        with patch("builtins.open") as mocked_open:
            _save_session_properties()
        mocked_open.assert_not_called()

    def test_save_session_properties__does_something(self):
        data_store.scenario[session_changed_key] = True
        props_file = f"{self.resources}/session.properties"
        data_store.scenario[session_file_key] = props_file
        data_store.scenario[session_keys_key] = ['a', 'b', 'c']
        data_store.scenario['a'] = '1'
        data_store.scenario['b'] = ''
        data_store.scenario['c'] = '{\n  "key": "value",\n  "else": "\\0x41"\n}'
        with patch("builtins.open", mock_open()) as mocked_open, patch("os.replace") as mocked_replace:
            _save_session_properties()
        mocked_open.assert_called_with(f"{props_file}.tmp", 'w')
        handle = mocked_open()
        handle.write.assert_has_calls([
            call('a = 1\n'),
            call('b = \n'),
            call('c = {\\n  "key": "value",\\n  "else": "\\\\0x41"\\n}\n')
        ])
        mocked_replace.assert_called_with(f"{props_file}.tmp", props_file)

    def test_store_in_session(self):
        data_store.scenario[session_keys_key] = list()
        _store_in_session("foo", "bar")
        self.assertEqual("bar", data_store.scenario["foo"])
        self.assertTrue(data_store.scenario[session_changed_key])
        self.assertTrue("foo" in data_store.scenario[session_keys_key])

    def test_save_file(self):
        body = b'abc'
        data_store.scenario.setdefault(response_key, {})['body'] = body
        with patch("builtins.open", mock_open()) as mocked_open:
            save_file("tests/downloads/image.png")
        mocked_open.assert_called_with(f"{self.test_dir}/downloads/image.png", 'wb')
        handle = mocked_open()
        handle.write.assert_called_with(body)

    def test_base64_encode(self):
        data_store.scenario[session_keys_key] = list()
        checkString = 'SSBhbSBhIHRlc3RzdHJpbmch'
        base64_encode("I am a teststring!", "placeholder")
        result = data_store.scenario.get("placeholder")
        self.assertEqual(checkString, result)

    def test_base64_decode(self):
        data_store.scenario[session_keys_key] = list()
        checkString = "I am a teststring!"
        base64_decode('SSBhbSBhIHRlc3RzdHJpbmch', "placeholder")
        result = data_store.scenario.get("placeholder")
        self.assertEqual(checkString, result)


if __name__ == '__main__':
    unittest.main()
