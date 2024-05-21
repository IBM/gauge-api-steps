#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import os

from http.client import HTTPResponse, responses
from getgauge.python import Messages
from urllib.error import HTTPError
from urllib.request import Request


def report_request_info(req: Request) -> None:
    do_report = os.environ.get('report_request', 'false').strip().lower() in ('true', '1')
    if not do_report:
        return
    print_and_report(f"> {req.get_method()} {req.get_full_url()}")
    for header_name, header_value in req.header_items():
        print_and_report(f"> {header_name}: {header_value}")
    if req.data is not None:
        print_and_report(">")
        print_and_report(f"> {req.data.decode()}")
    print_and_report(">")


def report_response_info(resp: HTTPResponse|HTTPError, resp_body: bytes) -> None:
    do_report = os.environ.get('report_response', 'false').strip().lower() in ('true', '1')
    if not do_report:
        return
    if resp is None or resp.status is None:
        print_and_report("< no reponse")
        print_and_report("<")
        return
    print_and_report(f"< {resp.status} {responses.get(resp.status, '')}")
    for header_name, header_value in resp.getheaders():
        print_and_report(f"< {header_name}: {header_value}")
    if len(resp_body) > 0:
        print_and_report("<")
        print_and_report(f"< {resp_body.decode()}")
    print_and_report("<")


def print_and_report(message: str) -> None:
    replace_whitespace = os.environ.get("replace_whitespace_in_console")
    console_message = message
    if replace_whitespace is not None:
        console_message = console_message.replace(' ', replace_whitespace)
        console_message = console_message.replace('\t', replace_whitespace * 4)
    print(console_message)
    Messages.write_message(message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\t', '    ').replace(' ', '&nbsp;'))
