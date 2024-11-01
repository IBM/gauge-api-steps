#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import base64
from types import NoneType
import numexpr
import json
import os
import re

from colorama import Fore
from diff_match_patch import diff_match_patch
from getgauge.python import data_store, step, after_scenario, before_scenario, ExecutionContext
from http.client import HTTPResponse
from io import BytesIO
from jsonpath_ng.ext import parse as parse_json_path
from lxml import etree
from typing import Any, Iterable
from urllib.request import HTTPCookieProcessor, HTTPRedirectHandler, OpenerDirector, Request, build_opener
from urllib.error import HTTPError
from .file_util import assert_file_is_in_project
from .reporting import print_and_report, report_request_info, report_response_info
from .session import load_session_properties, save_session_properties, store_in_session
from .substitute import substitute


opener_key = "_opener"
response_csrf_header_key = "_response_csrf_header"
request_csrf_header_key = "_request_csrf_header"
csrf_value_key = "_csrf_value"
body_key = "_body"
response_key = "_response"
headers_key = "_headers"
sent_request_headers_key = "_sent_request_headers"


@before_scenario
def beforescenario(context: ExecutionContext) -> None:
    session_file_param = os.environ.get("session_properties", "env/default/session.properties")
    session_file = substitute(session_file_param)
    load_session_properties(session_file)
    class DynamicRedirectHandler(HTTPRedirectHandler):

        def http_error_302(self, req, fp, code, msg, headers):
            # the property can be changed within a scenario, so both os.environ and data_store need to be considered.
            env_follow = os.environ.get("follow_redirects", "false")
            follow_redirects = data_store.scenario.get("follow_redirects", env_follow).lower() in ("true", "1")
            if follow_redirects:
                return super().http_error_302(req, fp, code, msg, headers)
            else:
                raise HTTPError(req.full_url, code, msg, headers, fp)
        http_error_301 = http_error_303 = http_error_307 = http_error_302
    opener: OpenerDirector = build_opener(HTTPCookieProcessor(), DynamicRedirectHandler())
    data_store.scenario[opener_key] = opener


@after_scenario
def afterscenario(context: ExecutionContext) -> None:
    save_session_properties()
    print_and_report(f"after scenario {context}")


@step("Response CSRF header <header>")
def resp_csrf_header(header_param: str) -> None:
    resp_csrf_header = substitute(header_param)
    store_in_session(response_csrf_header_key, resp_csrf_header)


@step("Request CSRF header <header>")
def req_csrf_header(header_param: str) -> None:
    req_csrf_header = substitute(header_param)
    data_store.scenario[request_csrf_header_key] = req_csrf_header


@step(["Store <key> <value>", "Store <key> = <value> in session"])
def store_in_session_step(key_param: str, value_param: str) -> None:
    key = substitute(key_param)
    value = substitute(value_param)
    store_in_session(key, value)


@step("Store <key> = <value> in scenario")
def store_in_scenario(key_param: str, value_param: str) -> None:
    key = substitute(key_param)
    value = substitute(value_param)
    data_store.scenario[key] = value


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
    print_and_report(message)


@step("Pretty print <json>")
def pretty_print(json_str_param: str) -> None:
    json_str = substitute(json_str_param)
    json_loaded = json.loads(json_str)
    pretty = json.dumps(json_loaded, indent=4)
    print_and_report(pretty)


@step("Print placeholders")
def print_placeholders() -> None:
    print_and_report(f"Environment: \n{os.environ}")
    print_and_report(f"Data store: \n{data_store.scenario}")


@step("Print headers")
def print_headers() -> None:
    headers: dict = data_store.scenario.get(sent_request_headers_key, {})
    print_and_report("Request headers:\n")
    for header_name, header_value in headers.items():
        print_and_report(f"    {header_name}: {header_value}")
    print_and_report("Response headers:\n")
    response_headers = data_store.scenario[response_key]["headers"]
    for header in response_headers:
        print_and_report(f"    {header[0]}: {header[1]}")


@step("Print status")
def print_status() -> None:
    status = data_store.scenario.get(response_key, {}).get("status")
    print_and_report(f"Response status:\n\n    {status}")


@step("Print body")
def print_body() -> None:
    body: bytes = data_store.scenario.get(response_key, {}).get("body")
    print_and_report("Response body:")
    if body is not None and len(body) > 0:
        try:
            json_loaded = json.loads(body.decode())
            pretty = json.dumps(json_loaded, indent=4)
            print_and_report(f"\n{pretty}".replace('\n', '\n    '))
        except (json.decoder.JSONDecodeError, UnicodeDecodeError):
            print_and_report(body.decode('unicode_escape'))


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
    data_store.scenario.setdefault(response_key, dict())["body"] = body.encode()


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
        body = body.encode()
    req = Request(url=url, method=method, headers=headers, data=body)
    data_store.scenario[sent_request_headers_key] = req.headers
    report_request_info(req)
    with _open(req) as r:
        resp: HTTPResponse|HTTPError = r
        resp_headers = resp.getheaders()
        resp_body = resp.read()
        report_response_info(resp, resp_body)
        data_store.scenario[response_key] = {
            "body": resp_body,
            "headers": resp_headers,
            "status": resp.status,
            "reason": resp.reason
        }
        if response_csrf_header_key in data_store.scenario:
            resp_csrf_header = data_store.scenario[response_csrf_header_key]
            for h in resp_headers:
                if h[0] == resp_csrf_header:
                    store_in_session(csrf_value_key, h[1])
                    break
        if hasattr(req, 'redirect_dict'):
            redirects_count = json.dumps(req.redirect_dict, indent=4)
            print_and_report(f"Redirections count (not in order): {redirects_count}")


@step("Assert status <status_code>")
def assert_response_status(status_code_param: str) -> None:
    status_code_str = substitute(status_code_param)
    status_code = int(status_code_str)
    response = data_store.scenario[response_key]
    actual = response['status']
    if status_code != actual:
        raise AssertionError(f"Assertion failed: Expected status code {status_code}, got {actual} - {response['reason']}\n{response['body']}")


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
    raise AssertionError(f"Assertion failed: Expected header {expected_header}: {expected_value} not found")


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
    if text not in str(match):
        raise AssertionError(f"Assertion failed: Expected text '{text}' not found in '{match}'")


@step("Assert xpath <xpath> contains <text>")
def assert_response_xpath_contains(xpath_param: str, text_param: str) -> None:
    xpath = substitute(xpath_param)
    text = substitute(text_param)
    match = _find_xpath_match_in_response(xpath)
    match_str = _text_from_xml(match)
    if text not in match_str:
        raise AssertionError(f"Assertion failed: Expected text '{text}' not found in '{match_str}'")


@step("Assert jsonpath <jsonpath> does not contain <text>")
def assert_response_jsonpath_does_not_contain(jsonpath_param: str, text_param: str) -> None:
    jsonpath = substitute(jsonpath_param)
    text = substitute(text_param)
    match = _find_jsonpath_match_in_response(jsonpath)
    if text in str(match):
        raise AssertionError(f"Assertion failed: Text '{text}' was found in '{match}'")


@step("Assert xpath <xpath> does not contain <text>")
def assert_response_xpath_does_not_contain(xpath_param: str, text_param: str) -> None:
    xpath = substitute(xpath_param)
    text = substitute(text_param)
    match = _find_xpath_match_in_response(xpath)
    match_str = _text_from_xml(match)
    if text in match_str:
        raise AssertionError(f"Assertion failed: Text '{text}' was found in '{match_str}'")


@step("Assert jsonpath <jsonpath> = <json_value>")
def assert_response_jsonpath_equals(jsonpath_param: str, json_value_param: str) -> None:
    jsonpath = substitute(jsonpath_param)
    value = substitute(json_value_param)
    match = _find_jsonpath_match_in_response(jsonpath)
    if os.environ.get("lenient_json_str_comparison", "false").lower() in ("true", "1"):
        if (not value.strip().startswith(('[', '{', '"',))) and (not is_numeric(value.strip())) and (value.strip() not in ('null','true','false',)):
            value  = f'"{value}"'
    value_json = json.loads(value)
    if match != value_json:
        diff = _diff_json(match, value_json)
        print_and_report(diff)
        raise AssertionError("Assertion failed: Expected value does not match")


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
    if not equal:
        print_and_report(f"Expected:\n{value}\nGot:\n{match_str}")
        raise AssertionError("Assertion failed: Expected value does not match")


@step("Assert jsonpath <jsonpath> type <type>")
def assert_response_jsonpath_type(jsonpath_param: str, json_type_param: str) -> None:
    jsonpath = substitute(jsonpath_param)
    json_type = substitute(json_type_param).lower()
    python_types = {
        "boolean": bool,
        "number": float,
        "integer": int,
        "string": str,
        "null": NoneType,
        "object": dict,
        "array": list,
    }
    python_type = python_types.get(json_type)
    if python_type is None:
        raise AssertionError(f"{json_type} is not a valid type. Valid: {', '.join(python_types.keys())}")
    match = _find_jsonpath_match_in_response(jsonpath)
    if not isinstance(match, python_type):
        actual_type = type(match).__name__
        match_str = json.dumps(match)
        match_str_short = match_str[0:60] if len(match_str) <= 60 else f"{match_str[0:60]}..."
        raise AssertionError(f"Assertion failed: {match_str_short} is of type {actual_type}, not {json_type}")


@step("Assert xpath <xpath> type <type>")
def assert_response_xpath_type(xpath_param: str, xml_type_param: str) -> None:
    xpath = substitute(xpath_param)
    xml_type = substitute(xml_type_param)
    allowed_types = (
        "boolean",
        "number",
        "integer",
        "string",
        "empty",
        "element",
        "attribute",
    )
    if xml_type not in allowed_types:
        raise AssertionError(f"{xml_type} is not a valid type. Valid: {', '.join(allowed_types)}")
    matches = _find_xpath_matches_in_response(xpath)
    num_matches = len(matches)
    if num_matches > 1:
        raise AssertionError(f"Assertion failed: multiple matches for {xpath} in {data_store.scenario[response_key]['body'].decode()}")
    if xml_type == "empty" and num_matches == 0:
        return
    match = matches[0]
    match_str = str(match)
    print_and_report(f"Expecting type {xml_type}. Actual python type: {type(match)}. Found match in xpath: {match_str}. XML-Attribute: {hasattr(match, 'attrname') and match.attrname is not None}")
    if xml_type == "integer" and is_numeric(match_str) and float(match_str).is_integer():
        return
    if xml_type == "number" and is_numeric(match_str):
        return
    if xml_type == "boolean" and match_str.lower() in ("true", "false"):
        return
    if xml_type == "empty" and len(match_str) == 0:
        return
    if xml_type == "string" and isinstance(match, str) and len(match_str) > 0:
        return
    if xml_type == "element" and isinstance(match, etree._Element):
        return
    if xml_type == "attribute" and hasattr(match, 'attrname') and match.attrname is not None:
        return
    match_str_short = match_str[0:60] if len(match_str) <= 60 else f"{match_str[0:60]}..."
    raise AssertionError(f"Assertion failed: {match_str_short} is not of type {xml_type}")


@step("Save jsonpath <jsonpath> as <key>")
def save_response_jsonpath(jsonpath_param: str, key_param: str) -> None:
    jsonpath = substitute(jsonpath_param)
    key = substitute(key_param)
    match = _find_jsonpath_match_in_response(jsonpath)
    match_str = match if isinstance(match, str) else json.dumps(match)
    store_in_session(key, match_str)


@step("Save xpath <xpath> as <key>")
def save_response_xpath(xpath_param: str, key_param: str) -> None:
    xpath = substitute(xpath_param)
    key = substitute(key_param)
    match = _find_xpath_match_in_response(xpath)
    match_primitive = match if not isinstance(match, etree._Element) else etree.tostring(match).decode()
    store_in_session(key, match_primitive)


@step("Save file <download>")
def save_file(download_param) -> None:
    download = substitute(download_param)
    download_path = assert_file_is_in_project(download)
    response_body = data_store.scenario[response_key]["body"]
    with open(download_path, 'wb') as d:
        d.write(response_body)


@step("Base64-encode <text> as <placeholder>")
def base64_encode(text_param: str, placeholder_param: str) -> None:
    print_and_report('Deprecated Step: Use placeholder substitutions like "!{base64:text}" or "!{base64urlsafe:text}" directly in Step parameters')
    text = substitute(text_param)
    placeholder = substitute(placeholder_param)
    bytesEncoded = text.encode()
    base = base64.b64encode(bytesEncoded)
    asString = base.decode()
    store_in_session(placeholder, asString)


@step("Base64-decode <text> as <placeholder>")
def base64_decode(text_param: str, placeholder_param: str) -> None:
    print_and_report('Deprecated Step: Use placeholder substitutions like "!{base64:text}" or "!{base64urlsafe:text}" directly in Step parameters')
    text = substitute(text_param)
    placeholder = substitute(placeholder_param)
    encodedText = text.encode()
    decodedBase = base64.b64decode(encodedText)
    asString = decodedBase.decode()
    store_in_session(placeholder, asString)


def _open(req: Request) -> HTTPResponse|HTTPError:
    opener: OpenerDirector = data_store.scenario[opener_key]
    try:
        return opener.open(req)
    except HTTPError as r:
        return r


def _find_jsonpath_match_in_response(jsonpath: str) -> Any:
    matches = _find_jsonpath_matches_in_response(jsonpath)
    if len(matches) == 0:
        raise AssertionError(f"Assertion failed: No value found at {jsonpath} in {data_store.scenario[response_key]['body'].decode()}")
    if len(matches) > 1:
        raise AssertionError(f"Assertion failed: multiple matches for {jsonpath} in {data_store.scenario[response_key]['body'].decode()}")
    return matches[0].value


def _find_jsonpath_matches_in_response(jsonpath: str) -> Iterable[Any]:
    resp: bytes = data_store.scenario[response_key]['body']
    resp_str = resp.decode()
    resp_json = json.loads(resp_str)
    jsonpath_expression = parse_json_path(jsonpath)
    match = jsonpath_expression.find(resp_json)
    return match


def _diff_json(match_json: bool|int|float|str|list|dict|None, expected_json: bool|int|float|str|list|dict|None) -> str:
    match_str = json.dumps(match_json, indent=4, sort_keys=True)
    expected_str = json.dumps(expected_json, indent=4, sort_keys=True)
    dmp = diff_match_patch()
    a = dmp.diff_linesToChars(match_str, expected_str)
    diffs = dmp.diff_main(a[0], a[1], False)
    dmp.diff_charsToLines(diffs, a[2])
    line_prefixes = {dmp.DIFF_DELETE: f'{Fore.RED}- ', dmp.DIFF_EQUAL: '  ', dmp.DIFF_INSERT: f'{Fore.GREEN}+ '}
    line_suffixes = {dmp.DIFF_DELETE: f'{Fore.RESET}', dmp.DIFF_EQUAL: '', dmp.DIFF_INSERT: f'{Fore.RESET}'}
    lines = []
    for d in diffs:
        prefix_key = d[0]
        prefix = line_prefixes[prefix_key]
        suffix = line_suffixes[prefix_key]
        diff_lines = d[1].removesuffix('\n').split('\n')
        for line in diff_lines:
            lines.append(f"{prefix}{line}{suffix}")
    return '\n'.join(lines)


def _find_xpath_match_in_response(xpath: str) -> etree._Element | str | int | float:
    matches = _find_xpath_matches_in_response(xpath)
    if len(matches) == 0:
        raise AssertionError(f"Assertion failed: No value found at {xpath} in {data_store.scenario[response_key]['body'].decode()}")
    if len(matches) > 1:
        raise AssertionError(f"Assertion failed: multiple matches for {xpath} in {data_store.scenario[response_key]['body'].decode()}")
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
    if not isinstance(result, bool):
        raise AssertionError(f"'{full_expr} = {result}' is not a boolean expression")
    if result is False:
        raise AssertionError(f"found {matches} matches, which is not {expr}")


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


def is_numeric(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False
