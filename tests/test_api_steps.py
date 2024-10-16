#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import contextlib
import io
import os
import unittest

from colorama import Fore
from getgauge.python import data_store
from unittest.mock import Mock, mock_open, patch
from tests import TEST_DIR, TEST_RESOURCES_DIR, TEST_OUT_DIR
from gauge_api_steps.api_steps import (
    opener_key, body_key, response_key, sent_request_headers_key,
    add_body, append_to_file, assert_response_jsonpath_equals, assert_response_jsonpath_type, assert_response_xpath_type,
    base64_decode, base64_encode, beforescenario, load_from_file, pretty_print, print_headers, print_status, print_body,
    save_file, simulate_response,
)


class TestApiSteps(unittest.TestCase):

    def setUp(self):
        data_store.scenario.clear()
        self.app_context = Mock()
        data_store.scenario["_session_keys"] = list()
        os.environ["GAUGE_PROJECT_ROOT"] = TEST_DIR
        os.environ["session_properties"] = f"{TEST_DIR}/session.properties"
        if not os.path.exists(TEST_OUT_DIR):
            os.mkdir(TEST_OUT_DIR)

    def test_beforescenario(self):
        beforescenario(self.app_context)
        self.assertIsNotNone(data_store.scenario[opener_key])

    def test_load_from_file(self):
        load_from_file(f"{TEST_RESOURCES_DIR}/file.txt", "testfile")
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
        out_file = f"{TEST_OUT_DIR}/output.csv"
        if os.path.isfile(out_file):
            os.remove(out_file)
        append_to_file(out_file, "a,b,c")
        append_to_file(out_file, "aa,bb,cc")
        with open(out_file) as f:
            contents = f.read()
        self.assertEqual("a,b,c\naa,bb,cc\n", contents, f"got unexpected content in output file {out_file}")

    def test_append_fails(self):
        out_file = "notvalid/output.csv"
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

    def test_assert_response_jsonpath_equals_with_json_stucture(self):
        json_str = '{"a": {"b": "value"}}'
        data_store.scenario[response_key] = {'body': json_str.encode()}
        assert_response_jsonpath_equals("$", json_str)

    def test_assert_response_jsonpath_equals_with_json_str(self):
        data_store.scenario[response_key] = {'body': '{"a": {"b": "value"}}'.encode()}
        assert_response_jsonpath_equals("$.a.b", '"value"')

    def test_assert_response_jsonpath_equals_with_lenient_json_str(self):
        os.environ["lenient_json_str_comparison"] = "True"
        body = """{
          "a": {
            "b": "value"
          },
          "b": null,
          "c": 1,
          "d": true,
          "e": false,
          "f": []
        }"""
        data_store.scenario[response_key] = {"body": body.encode()}
        params = [("$.a.b", "value",), ("$.a.b", '"value"',), ("$.b", "null",), ("$.c", "1",), ("$.d", "true",), ("$.e", "false",), ("$.f", "[]",)]
        for json_path, value in params:
            with self.subTest(json_path=json_path, value=value):
                assert_response_jsonpath_equals(json_path, value)
        # TODO: check (true, false, null, {, [, ", float, int) are not quoted

    def test_assert_response_jsonpath_equals_fails_and_shows_diff(self):
        response = """
        {
          "a": "a",
          "b": 1,
          "c": [
            1, 2, 3
          ]
        }
        """
        expected = """
        {
          "a": "a",
          "b": 2,
          "c": [
            1, 2, 3, 4
          ]
        }
        """
        diff = '\n'.join((
            '  {',
            '      "a": "a",',
            f'{Fore.RED}-     "b": 1,{Fore.RESET}',
            f'{Fore.GREEN}+     "b": 2,{Fore.RESET}',
            '      "c": [',
            '          1,',
            '          2,',
            f'{Fore.RED}-         3{Fore.RESET}',
            f'{Fore.GREEN}+         3,{Fore.RESET}',
            f'{Fore.GREEN}+         4{Fore.RESET}',
            '      ]',
            '  }\n',))
        data_store.scenario[response_key] = {'body': response.encode()}
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            self.assertRaises(AssertionError, lambda: assert_response_jsonpath_equals("$", expected))
            self.assertEqual(diff, buf.getvalue())

    def test_assert_response_jsonpath_type(self):
        response = """
        {
          "integer": 2,
          "number": 1.1,
          "boolean": true,
          "string": "a string",
          "null": null,
          "array": [],
          "object": {}
        }
        """
        data_store.scenario[response_key] = {'body': response.encode()}
        params = ["integer", "number", "boolean", "string", "null", "array", "object"]
        for json_type in params:
            jsonpath = f"$.{json_type}"
            with self.subTest(jsonpath=jsonpath, json_type=json_type):
                assert_response_jsonpath_type(jsonpath, json_type)

    def test_assert_response_jsonpath_type__fails(self):
        response = """
        {
          "number": 1.1
        }
        """
        data_store.scenario[response_key] = {'body': response.encode()}
        params = ["integer", "num", "boolean", "string", "null", "array", "object"]
        for json_type in params:
            jsonpath = "$.number"
            with self.subTest(jsonpath=jsonpath, json_type=json_type):
                self.assertRaises(AssertionError, lambda: assert_response_jsonpath_type(jsonpath, json_type))

    def test_assert_response_xpath_type(self):
        response = """
        <root attribute="attribute_value">
          <boolean>False</boolean>
          <number>1.1</number>
          <integer>2</integer>
          <string>abc</string>
          <empty></empty>
          <element><branch></branch></element>
        </root>
        """
        data_store.scenario[response_key] = {'body': response.encode()}
        params = [
            ("integer", "/root/integer/node()"),
            ("number", "/root/number/node()"),
            ("boolean", "/root/boolean/node()"),
            ("string", "/root/string/node()"),
            ("empty", "/root/empty/node()"),
            ("element", "/root/element/branch"),
            ("attribute", "/root/@attribute")
        ]
        for xml_type, xpath in params:
            with self.subTest(xpath = xpath, xml_type = xml_type):
                assert_response_xpath_type(xpath, xml_type)

    def test_assert_response_xpath_type__fails(self):
        response = """
        <root>
          <number>1.1</number>
        </root>
        """
        data_store.scenario[response_key] = {'body': response.encode()}
        params = ["integer", "number", "boolean", "string", "empty", "attribute"]
        for xml_type in params:
            xpath = "/root/number"
            with self.subTest(xpath=xpath, xml_type=xml_type):
                self.assertRaises(AssertionError, lambda: assert_response_xpath_type(xpath, xml_type))

    def test_save_file(self):
        body = b'abc'
        data_store.scenario.setdefault(response_key, {})['body'] = body
        with patch("builtins.open", mock_open()) as mocked_open:
            save_file("tests/downloads/image.png")
        mocked_open.assert_called_with(f"{TEST_DIR}/downloads/image.png", 'wb')
        handle = mocked_open()
        handle.write.assert_called_with(body)

    def test_base64_encode(self):
        checkString = 'SSBhbSBhIHRlc3RzdHJpbmch'
        base64_encode("I am a teststring!", "placeholder")
        result = data_store.scenario.get("placeholder")
        self.assertEqual(checkString, result)

    def test_base64_decode(self):
        checkString = "I am a teststring!"
        base64_decode('SSBhbSBhIHRlc3RzdHJpbmch', "placeholder")
        result = data_store.scenario.get("placeholder")
        self.assertEqual(checkString, result)


if __name__ == '__main__':
    unittest.main()
