#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import unittest

from http.client import HTTPResponse
from getgauge.registry import MessagesStore
from textwrap import dedent
from unittest.mock import call, patch, Mock
from urllib.request import Request
from gauge_api_steps.reporting import print_and_report, report_request_info, report_response_info


class TestReporting(unittest.TestCase):

    def setUp(self):
        MessagesStore.clear()

    def tearDown(self):
        MessagesStore.clear()

    def test_print_and_report(self):
        MessagesStore.clear()
        with patch('builtins.print') as mock_print, patch('os.environ', {"replace_whitespace_in_report": "-"}):
            print_and_report("abc")
            print_and_report("a b")
            print_and_report("a\tb")
            print_and_report("<>")
        self.assertEqual([call("abc"), call("a-b"), call("a----b"), call("<>")], mock_print.mock_calls)
        self.assertEqual(["abc", "a-b", "a----b", "&lt;&gt;"], MessagesStore.pending_messages())

    def test_report_request_info(self):
        req = Request(url="http://localhost", method="POST", headers={"Content-Type": "image/png"}, data=b"abc\ndef")
        with patch('builtins.print') as mock_print, patch('os.environ', {"report_request": "true"}):
            report_request_info(req)
        result = "\n".join([c.args[0] for c in mock_print.mock_calls])
        self.assertEqual(dedent("""
            > POST http://localhost
            > Content-type: image/png
            >
            > abc
            def
            >""").lstrip(),
            result
        )

    def test_report_response_info(self):
        resp = Mock(HTTPResponse)
        resp.configure_mock(**{'getheaders.return_value': [("Content-type", "image/png",),], 'status': 200})
        with patch('builtins.print') as mock_print, patch('os.environ', {"report_response": "true"}):
            report_response_info(resp, b"abc\ndef")
        result = "\n".join([c.args[0] for c in mock_print.mock_calls])
        self.assertEqual(dedent("""
            < 200 OK
            < Content-type: image/png
            <
            < abc
            def
            <""").lstrip(),
            result
        )


if __name__ == '__main__':
    unittest.main()
