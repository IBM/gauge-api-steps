#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import base64
import numexpr
import json
import os
import re

from getgauge.python import data_store, step, after_scenario, before_scenario, ExecutionContext, Messages
from io import BytesIO
from jsonpath_ng.ext import parse as parse_json_path
from lxml import etree
from typing import Any, Iterable
from urllib.request import HTTPCookieProcessor, OpenerDirector, Request, build_opener
from urllib.response import addinfourl as Response
from urllib.error import HTTPError
from .file_util import assert_file_is_in_project
from .substitute import substitute


opener_key = "_opener"
response_csrf_header_key = "_response_csrf_header"
request_csrf_header_key = "_request_csrf_header"
csrf_value_key = "_csrf_value"
body_key = "_body"
response_key = "_response"
headers_key = "_headers"
sent_request_headers_key = "_sent_request_headers"
session_changed_key = "_session_changed"
session_file_key = "_session_file"
session_keys_key = "_session_keys"


@before_scenario
def beforescenario(context: ExecutionContext) -> None:
    _load_session_properties()
    opener: OpenerDirector = build_opener(HTTPCookieProcessor())
    data_store.scenario[opener_key] = opener


@after_scenario
def afterscenario(context: ExecutionContext) -> None:
    _save_session_properties()
    _print_and_report(f"after scenario {context}")


@step("Response CSRF header <header>")
def resp_csrf_header(header_param: str) -> None:
    resp_csrf_header = substitute(header_param)
    _store_in_session(response_csrf_header_key, resp_csrf_header)


@step("Request CSRF header <header>")
def req_csrf_header(header_param: str) -> None:
    req_csrf_header = substitute(header_param)
    data_store.scenario[request_csrf_header_key] = req_csrf_header


@step("Store <key> <value>")
def store(key_param: str, value_param: str) -> None:
    key = substitute(key_param)
    value = substitute(value_param)
    _store_in_session(key, value)


@step("Load from file <file> as <placeholder>")
def load_from_file(file_param, placeholder_param) -> None:
    file_name = substitute(file_param)
    placeholder_name = substitute(placeholder_param)
    file_path = assert_file_is_in_project(file_name)
    with open(file_path, 'r') as f:
        content = f.read()
    data_store.scenario[placeholder_name] = content


@step("Print <message>")
def print_message(message_param: str) -> None:
    message = substitute(message_param)
    _print_and_report(message)


@step("Pretty print <json>")
def pretty_print(json_str_param: str) -> None:
    json_str = substitute(json_str_param)
    json_loaded = json.loads(json_str)
    pretty = json.dumps(json_loaded, indent=4)
    _print_and_report(pretty)


@step("Print placeholders")
def print_placeholders() -> None:
    _print_and_report(f"Environment: \n{os.environ}")
    _print_and_report(f"Data store: \n{data_store.scenario}")


@step("Print headers")
def print_headers() -> None:
    headers: dict = data_store.scenario.get(sent_request_headers_key, {})
    _print_and_report("Request headers:\n")
    for header_name, header_value in headers.items():
        _print_and_report(f"    {header_name}: {header_value}")
    _print_and_report("Response headers:\n")
    response_headers = data_store.scenario[response_key]["headers"]
    for header in response_headers:
        _print_and_report(f"    {header[0]}: {header[1]}")


@step("Print status")
def print_status() -> None:
    status = data_store.scenario.get(response_key, {}).get("status")
    _print_and_report(f"Response status:\n\n    {status}")


@step("Print body")
def print_body() -> None:
    body: bytes = data_store.scenario.get(response_key, {}).get("body")
    _print_and_report("Response body:")
    if body is not None and len(body) > 0:
        try:
            json_loaded = json.loads(body.decode('UTF-8'))
            pretty = json.dumps(json_loaded, indent=4)
            _print_and_report(f"\n{pretty}".replace('\n', '\n    '))
        except json.decoder.JSONDecodeError:
            _print_and_report(body.decode('UTF-8'))


@step("Append to <file>: <value>")
def append_to_file(file_param: str, value_param: str) -> None:
    file_name = substitute(file_param)
    file_path = assert_file_is_in_project(file_name)
    value = substitute(value_param)
    with open(file_path, 'a') as f:
        f.write(f"{value}\n")


@step("With header <header>: <value>")
def add_header(header_param: str, value_param: str) -> None:
    header = substitute(header_param)
    value = substitute(value_param)
    headers = data_store.scenario.setdefault(headers_key, {})
    headers[header] = value


@step("With body <body>")
def add_body(body_param: str) -> None:
    body = substitute(body_param)
    data_store.scenario[body_key] = body


@step("Simulate response body: <value>")
def simulate_response(body_param: str) -> None:
    body = substitute(body_param)
    data_store.scenario.setdefault(response_key, dict())["body"] = body


@step("Request <method> <url>")
def make_request(method_param: str, url_param: str) -> None:
    method = substitute(method_param)
    url = substitute(url_param)
    headers = data_store.scenario.pop(headers_key, {})
    if request_csrf_header_key in data_store.scenario and csrf_value_key in data_store.scenario:
        req_csrf_header = data_store.scenario[request_csrf_header_key]
        headers[req_csrf_header] = data_store.scenario[csrf_value_key]
    body = data_store.scenario.pop(body_key, None)
    if isinstance(body, str):
        body = body.encode('UTF-8')
    req = Request(url=url, method=method, headers=headers, data=body)
    data_store.scenario[sent_request_headers_key] = req.headers
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
                    _store_in_session(csrf_value_key, h[1])
                    break


@step("Assert status <status_code>")
def assert_response_status(status_code_param: str) -> None:
    status_code_str = substitute(status_code_param)
    status_code = int(status_code_str)
    response = data_store.scenario[response_key]
    actual = response['status']
    assert status_code == actual, \
        f"Assertion failed: Expected status code {status_code}, got {actual} - {response['reason']}\n{response['body']}"


@step("Assert header <header>: <value>")
def assert_header(header_param: str, value_param: str) -> None:
    expected_header = substitute(header_param).upper()
    expected_value = substitute(value_param)
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
    jsonpath = substitute(jsonpath_param)
    # will fail, if it is not found or it is found more than once
    _find_jsonpath_match_in_response(jsonpath)


@step("Assert xpath <xpath> exists")
def assert_response_xpath_exists(xpath_param: str) -> None:
    xpath = substitute(xpath_param)
    # will fail, if it is not found or it is found more than once
    _find_xpath_match_in_response(xpath)


@step("Assert jsonpath <jsonpath> exists <expr>")
def assert_response_jsonpath_exists_expr(jsonpath_param: str, expr_param: str) -> None:
    jsonpath = substitute(jsonpath_param)
    expr = substitute(expr_param)
    matches = _find_jsonpath_matches_in_response(jsonpath)
    _eval_matches_length(len(matches), expr)


@step("Assert xpath <xpath> exists <expr>")
def assert_response_xpath_exists_expr(xpath_param: str, expr_param: str) -> None:
    xpath = substitute(xpath_param)
    expr = substitute(expr_param)
    matches = _find_xpath_matches_in_response(xpath)
    _eval_matches_length(len(matches), expr)


@step("Assert jsonpath <jsonpath> contains <text>")
def assert_response_jsonpath_contains(jsonpath_param: str, text_param: str) -> None:
    jsonpath = substitute(jsonpath_param)
    text = substitute(text_param)
    match = _find_jsonpath_match_in_response(jsonpath)
    assert text in str(match), \
        f"Assertion failed: Expected text '{text}' not found in '{match}'"


@step("Assert xpath <xpath> contains <text>")
def assert_response_xpath_contains(xpath_param: str, text_param: str) -> None:
    xpath = substitute(xpath_param)
    text = substitute(text_param)
    match = _find_xpath_match_in_response(xpath)
    match_str = _text_from_xml(match)
    assert text in match_str, \
        f"Assertion failed: Expected text '{text}' not found in '{match_str}'"


@step("Assert jsonpath <jsonpath> does not contain <text>")
def assert_response_jsonpath_does_not_contain(jsonpath_param: str, text_param: str) -> None:
    jsonpath = substitute(jsonpath_param)
    text = substitute(text_param)
    match = _find_jsonpath_match_in_response(jsonpath)
    assert text not in str(match), \
        f"Assertion failed: Text '{text}' was found in '{match}'"


@step("Assert xpath <xpath> does not contain <text>")
def assert_response_xpath_does_not_contain(xpath_param: str, text_param: str) -> None:
    xpath = substitute(xpath_param)
    text = substitute(text_param)
    match = _find_xpath_match_in_response(xpath)
    match_str = _text_from_xml(match)
    assert text not in match_str, \
        f"Assertion failed: Text '{text}' was found in '{match_str}'"


@step("Assert jsonpath <jsonpath> = <json_value>")
def assert_response_jsonpath_equals(jsonpath_param: str, json_value_param: str) -> None:
    jsonpath = substitute(jsonpath_param)
    value = substitute(json_value_param)
    match = _find_jsonpath_match_in_response(jsonpath)
    value_json = json.loads(value)
    assert match == value_json, \
        f"Assertion failed: Expected value '{value}' does not match '{match}'"


@step("Assert xpath <xpath> = <xml_value>")
def assert_response_xpath_equals(xpath_param: str, xml_value_param: str) -> None:
    xpath = substitute(xpath_param)
    value = substitute(xml_value_param)
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
    jsonpath = substitute(jsonpath_param)
    key = substitute(key_param)
    match = _find_jsonpath_match_in_response(jsonpath)
    match_str = match if isinstance(match, str) else json.dumps(match)
    _store_in_session(key, match_str)


@step("Save xpath <xpath> as <key>")
def save_response_xpath(xpath_param: str, key_param: str) -> None:
    xpath = substitute(xpath_param)
    key = substitute(key_param)
    match = _find_xpath_match_in_response(xpath)
    match_primitive = match if not isinstance(match, etree._Element) else etree.tostring(match).decode('UTF-8')
    _store_in_session(key, match_primitive)


@step("Save file <download>")
def save_file(download_param) -> None:
    download = substitute(download_param)
    download_path = assert_file_is_in_project(download)
    response_body = data_store.scenario[response_key]["body"]
    with open(download_path, 'wb') as d:
        d.write(response_body)


@step("Base64-encode <text> as <placeholder>")
def base64_encode(text_param: str, placeholder_param: str) -> None:
    text = substitute(text_param)
    placeholder = substitute(placeholder_param)
    bytesEncoded = text.encode('utf-8')
    base = base64.b64encode(bytesEncoded)
    asString = base.decode('utf-8')
    _store_in_session(placeholder, asString)

@step("Base64-decode <text> as <placeholder>")
def base64_decode(text_param: str, placeholder_param: str) -> None:
    text = substitute(text_param)
    placeholder = substitute(placeholder_param)
    encodedText = text.encode('utf-8')
    decodedBase = base64.b64decode(encodedText)
    asString = decodedBase.decode('utf-8')
    _store_in_session(placeholder, asString)
    

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


def _print_and_report(message: str) -> None:
    replace_whitespace = os.environ.get("replace_whitespace_in_report")
    if replace_whitespace is not None:
        message = message.replace(' ', replace_whitespace)
        message = message.replace('\t', replace_whitespace * 4)
    print(message)
    Messages.write_message(message.replace('<', '&lt;'))


def _load_session_properties() -> None:
    session_file_param = os.environ.get("session_properties", "env/default/session.properties")
    session_file = substitute(session_file_param)
    session_file_path = assert_file_is_in_project(session_file)
    data_store.scenario[session_file_key] = session_file_path
    data_store.scenario[session_keys_key] = list()
    if not os.path.exists(session_file_path):
        return
    with open(session_file_path) as s:
        for line in s.readlines():
            split = line.split("=", 1)
            key = split[0].strip()
            value = _decode_value(split[1].strip()) if len(split) >= 2 else None
            _store_in_session(key, value, False)


def _save_session_properties() -> None:
    session_changed: bool = data_store.scenario.get(session_changed_key, False)
    session_file_path: str = data_store.scenario.get(session_file_key)
    session_keys: list = data_store.scenario.get(session_keys_key)
    if not session_changed or session_file_path is None or session_keys is None:
        return
    tmp = f"{session_file_path}.tmp"
    with open(tmp, 'w') as session:
        for key in session_keys:
            value: str = data_store.scenario.get(key)
            if value is not None:
                value = _encode_value(value)
                session.write(f'{key} = {value}\n')
    os.replace(tmp, session_file_path)


def _encode_value(value: str) -> str:
    """ this transforms any string into a JSON-like str, but keeps non-ascii characters as is. """
    if value is None:
        return None
    value = value.replace('\\', '\\\\')
    value = value.replace('"', '\\"')
    value = value.replace('\n', '\\n')
    return f'"{value}"'


def _decode_value(value: str) -> str:
    """ decodes a JSON-like str. """
    if value is not None and len(value) >= 2:
        value = value[1:-1]
        value = value.replace('\\n', '\n')
        value = value.replace('\\"', '"')
        value = value.replace('\\\\', '\\')
    return value


def _store_in_session(key: str, value: str, changed: bool=True) -> None:
    data_store.scenario[session_changed_key] = changed
    data_store.scenario[key] = value
    session_keys: list = data_store.scenario[session_keys_key]
    if key not in session_keys:
        session_keys.append(key)
