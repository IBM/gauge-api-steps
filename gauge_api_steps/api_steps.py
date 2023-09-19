#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import json
import os
import re

from getgauge.python import data_store, step, after_scenario, before_scenario, ExecutionContext, Messages
from io import BytesIO
from jsonpath_ng import parse as parse_json_path
from lxml import etree
import numexpr
from string import Template
from typing import Any, Iterable
from urllib.request import HTTPCookieProcessor, OpenerDirector, Request, build_opener
from urllib.response import addinfourl as Response
from urllib.error import HTTPError


opener_key = "_opener"
response_csrf_header_key = "_response_csrf_header"
request_csrf_header_key = "_request_csrf_header"
csrf_value_key = "_csrf_value"
body_key = "_body"
response_key = "_response"
headers_key = "_headers"


@before_scenario
def beforescenario(context: ExecutionContext) -> None:
    opener: OpenerDirector = build_opener(HTTPCookieProcessor())
    data_store.scenario[opener_key] = opener


@after_scenario
def afterscenario(context: ExecutionContext) -> None:
    _print_and_report(f"after scenario {context}")


@step("Response CSRF header <header>")
def resp_csrf_header(header_param: str) -> None:
    resp_csrf_header = _substitute(header_param)
    data_store.scenario[response_csrf_header_key] = resp_csrf_header


@step("Request CSRF header <header>")
def req_csrf_header(header_param: str) -> None:
    req_csrf_header = _substitute(header_param)
    data_store.scenario[request_csrf_header_key] = req_csrf_header


@step("Store <key> <value>")
def store(key: str, value: str) -> None:
    data_store.scenario[key] = value


@step("Print <message>")
def print_message(message_param: str) -> None:
    message = _substitute(message_param)
    _print_and_report(message)


@step("Print placeholders")
def print_placeholders() -> None:
    _print_and_report(f"{os.environ}")
    _print_and_report(f"{data_store.scenario}")


@step("Append to <file>: <value>")
def append_to_file(file_param: str, value_param: str):
    file_path = os.path.realpath(_substitute(file_param))
    project_root = os.path.realpath(os.environ.get("GAUGE_PROJECT_ROOT"))
    assert file_path.startswith(project_root), f"file must be inside {project_root}"
    value = _substitute(value_param)
    with open(file_path, 'a') as f:
        f.write(f"{value}\n")


@step("With header <header>: <value>")
def add_header(header_param: str, value_param: str) -> None:
    header = _substitute(header_param)
    value = _substitute(value_param)
    headers = data_store.scenario.setdefault(headers_key, {})
    headers[header] = value


@step("With body <body>")
def add_body(body_param: str) -> None:
    body = _substitute(body_param)
    data_store.scenario[body_key] = bytes(body, "utf8")


@step("Request <method> <url>")
def make_request(method_param: str, url_param: str) -> None:
    method = _substitute(method_param)
    url = _substitute(url_param)
    headers = data_store.scenario.pop(headers_key, {})
    if request_csrf_header_key in data_store.scenario and csrf_value_key in data_store.scenario:
        req_csrf_header = data_store.scenario[request_csrf_header_key]
        headers[req_csrf_header] = data_store.scenario[csrf_value_key]
    body = data_store.scenario.pop(body_key, None)
    req = Request(url=url, method=method, headers=headers, data=body)
    with _open(req) as resp:
        resp_headers = resp.getheaders()
        data_store.scenario[response_key] = {
            "body": resp.read(),
            "headers": resp_headers,
            "status": resp.status,
            "reason": resp.reason
        }
        if response_csrf_header_key in data_store.scenario:
            resp_csrf_header = data_store.scenario[response_csrf_header_key]
            for h in resp_headers:
                if h[0] == resp_csrf_header:
                    data_store.scenario[csrf_value_key] = h[1]
                    break


@step("Assert status <status_code>")
def assert_response_status(status_code_param: str) -> None:
    status_code_str = _substitute(status_code_param)
    status_code = int(status_code_str)
    response = data_store.scenario[response_key]
    actual = response['status']
    assert status_code == actual, \
        f"Assertion failed: Expected status code {status_code}, got {actual} - {response['reason']}\n{response['body']}"


@step("Assert header <header>: <value>")
def assert_header(header_param: str, value_param: str) -> None:
    expected_header = _substitute(header_param).upper()
    expected_value = _substitute(value_param)
    response = data_store.scenario[response_key]
    headers = response['headers']
    for header in headers:
        header_name = header[0].upper()
        header_value = header[1]
        if expected_header != header_name:
            continue
        header_value = header[1]
        if expected_value == header_value:
            return
        header_values = header[1].split(',')
        for header_value in header_values:
            header_value = header_value.strip()
            if expected_value == header_value:
                return
    raise AssertionError (f"Assertion failed: Expected header {expected_header}: {expected_value} not found")


@step("Assert jsonpath <jsonpath> exists")
def assert_response_jsonpath_exists(jsonpath_param: str) -> None:
    jsonpath = _substitute(jsonpath_param)
    # will fail, if it is not found or it is found more than once
    _find_jsonpath_match_in_response(jsonpath)


@step("Assert xpath <xpath> exists")
def assert_response_xpath_exists(xpath_param: str) -> None:
    xpath = _substitute(xpath_param)
    # will fail, if it is not found or it is found more than once
    _find_xpath_match_in_response(xpath)


@step("Assert jsonpath <jsonpath> exists <expr>")
def assert_response_jsonpath_exists_expr(jsonpath_param: str, expr_param: str) -> None:
    jsonpath = _substitute(jsonpath_param)
    expr = _substitute(expr_param)
    matches = _find_jsonpath_matches_in_response(jsonpath)
    _eval_matches_length(len(matches), expr)


@step("Assert xpath <xpath> exists <expr>")
def assert_response_xpath_exists_expr(xpath_param: str, expr_param: str) -> None:
    xpath = _substitute(xpath_param)
    expr = _substitute(expr_param)
    matches = _find_xpath_matches_in_response(xpath)
    _eval_matches_length(len(matches), expr)


@step("Assert jsonpath <jsonpath> contains <text>")
def assert_response_jsonpath_contains(jsonpath_param: str, text_param: str) -> None:
    jsonpath = _substitute(jsonpath_param)
    text = _substitute(text_param)
    match = _find_jsonpath_match_in_response(jsonpath)
    assert text in str(match), \
        f"Assertion failed: Expected text '{text}' not found in '{match}'"


@step("Assert xpath <xpath> contains <text>")
def assert_response_xpath_contains(xpath_param: str, text_param: str) -> None:
    xpath = _substitute(xpath_param)
    text = _substitute(text_param)
    match = _find_xpath_match_in_response(xpath)
    match_str = _text_from_xml(match)
    assert text in match_str, \
        f"Assertion failed: Expected text '{text}' not found in '{match_str}'"


@step("Assert jsonpath <jsonpath> does not contain <text>")
def assert_response_jsonpath_does_not_contain(jsonpath_param: str, text_param: str) -> None:
    jsonpath = _substitute(jsonpath_param)
    text = _substitute(text_param)
    match = _find_jsonpath_match_in_response(jsonpath)
    assert text not in str(match), \
        f"Assertion failed: Text '{text}' was found in '{match}'"


@step("Assert xpath <xpath> does not contain <text>")
def assert_response_xpath_does_not_contain(xpath_param: str, text_param: str) -> None:
    xpath = _substitute(xpath_param)
    text = _substitute(text_param)
    match = _find_xpath_match_in_response(xpath)
    match_str = _text_from_xml(match)
    assert text not in match_str, \
        f"Assertion failed: Text '{text}' was found in '{match_str}'"


@step("Assert jsonpath <jsonpath> = <json_value>")
def assert_response_jsonpath_equals(jsonpath_param: str, json_value_param: str) -> None:
    jsonpath = _substitute(jsonpath_param)
    value = _substitute(json_value_param)
    match = _find_jsonpath_match_in_response(jsonpath)
    value_json = json.loads(value)
    assert match == value_json, \
        f"Assertion failed: Expected value '{value}' does not match '{match}'"


@step("Assert xpath <xpath> = <xml_value>")
def assert_response_xpath_equals(xpath_param: str, xml_value_param: str) -> None:
    xpath = _substitute(xpath_param)
    value = _substitute(xml_value_param)
    match = _find_xpath_match_in_response(xpath)
    match_str: str
    if isinstance(match, etree._Element):
        value_xml = etree.XML(value)
        match_str = match.xpath("string(.)")
        equal = _xml_elements_equal(match, value_xml)
    else:
        match = _text_from_xml(match)
        match_str = match
        equal = match == value
    assert equal, \
        f"Assertion failed: Expected value '{value}' does not match '{match_str}'"


@step("Save jsonpath <jsonpath> as <key>")
def save_response_jsonpath(jsonpath_param: str, key_param: str) -> None:
    jsonpath = _substitute(jsonpath_param)
    key = _substitute(key_param)
    match = _find_jsonpath_match_in_response(jsonpath)
    data_store.scenario[key] = match


@step("Save xpath <xpath> as <key>")
def save_response_xpath(xpath_param: str, key_param: str) -> None:
    xpath = _substitute(xpath_param)
    key = _substitute(key_param)
    match = _find_xpath_match_in_response(xpath)
    data_store.scenario[key] = match


def _open(req: Request) -> Response:
    opener: OpenerDirector = data_store.scenario[opener_key]
    try:
        return opener.open(req)
    except HTTPError as r:
        return r


def _find_jsonpath_match_in_response(jsonpath: str) -> Any:
    matches = _find_jsonpath_matches_in_response(jsonpath)
    assert len(matches) > 0, \
        f"Assertion failed: No value found at {jsonpath} in {data_store.scenario[response_key]['body'].decode('UTF-8')}"
    assert len(matches) == 1, \
        f"Assertion failed: multiple matches for {jsonpath} in {data_store.scenario[response_key]['body'].decode('UTF-8')}"
    return matches[0].value


def _find_jsonpath_matches_in_response(jsonpath: str) -> Iterable[Any]:
    resp: bytes = data_store.scenario[response_key]['body']
    resp_str = resp.decode('UTF-8')
    resp_json = json.loads(resp_str)
    jsonpath_expression = parse_json_path(jsonpath)
    match = jsonpath_expression.find(resp_json)
    return match


def _find_xpath_match_in_response(xpath: str) -> etree._Element | str | int | float:
    matches = _find_xpath_matches_in_response(xpath)
    assert len(matches) > 0, \
        f"Assertion failed: No value found at {xpath} in {data_store.scenario[response_key]['body'].decode('UTF-8')}"
    assert len(matches) == 1, \
        f"Assertion failed: multiple matches for {xpath} in {data_store.scenario[response_key]['body'].decode('UTF-8')}"
    return matches[0]


def _find_xpath_matches_in_response(xpath: str) -> Iterable[etree._Element] | Iterable[str] | Iterable[int] | Iterable[float]:
    resp: bytes = data_store.scenario[response_key]['body']
    file_like_body = BytesIO(resp)
    tree: etree._ElementTree = etree.parse(file_like_body)
    root: etree._Element = tree.getroot()
    _clear_namespaces(root)
    match = root.xpath(xpath)
    return match if isinstance(match, list) else [match]


def _clear_namespaces(elem: etree._Element) -> None:
    # lxml with xpath cannot properly handle default namespaces.
    # In our case, we probably do not need namespace handling, as we only look at single files, which are mostly pretty simple.
    elem.tag = re.sub("{.*}", "", elem.tag)
    for child in elem.getchildren():
        _clear_namespaces(child)


def _eval_matches_length(matches: int, expr: str) -> None:
    full_expr = f"{matches}{expr}"
    result = numexpr.evaluate(full_expr).tolist()
    assert isinstance(result, bool), f"'{full_expr} = {result}' is not a boolean expression"
    assert result is True, f"found {matches} matches, which is not {expr}"


def _text_from_xml(match: etree._Element | str | int | float) -> str:
    if isinstance(match, etree._Element):
        return match.xpath('string(.)')
    else:
        return str(match)


def _xml_elements_equal(e1: etree._Element, e2: etree._Element) -> bool:
    """ https://stackoverflow.com/questions/7905380/testing-equivalence-of-xml-etree-elementtree """
    if e1.tag != e2.tag: return False
    if e1.text != e2.text: return False
    if e1.tail != e2.tail: return False
    if e1.attrib != e2.attrib: return False
    if len(e1) != len(e2): return False
    return all(_xml_elements_equal(c1, c2) for c1, c2 in zip(e1, e2))


def _substitute(gauge_param: str) -> str:
    template = Template(gauge_param)
    #pipe operator does not work on windows
    substituted = template.safe_substitute(os.environ)
    template = Template(substituted)
    substituted = template.safe_substitute(data_store.scenario)
    return substituted


def _print_and_report(message: str) -> None:
    print(message)
    Messages.write_message(message.replace('<', '&lt;'))
