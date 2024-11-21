#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import base64
import json
import numexpr
import os
import uuid

from datetime import datetime
from getgauge.python import data_store
from numpy import array2string
from string import Template
from typing import Callable
from urllib import parse as urlcodec
from .file_util import assert_file_is_in_project
from .session import session_properties


def substitute(gauge_param: str) -> str:
    """Substitutes placeholders in a step parameter with values from environment variables
    and evaluates mathematical expressions.
    The environment variables are usually defined in the env/*.properties files in the gauge project
    or are placed into the context with specific steps.
    So the same placeholder can be replaced with different values in different environments.
    Examples:
    * Print "${base_url}/home"
    * Print "5 + 6 = #{5 + 6}"
    * Print "5 + ${addend} = #{5 + $addend}"
    * Print "!{file:resources/body.json}"
    In the first example, the placeholder `base_url` will be substituted by the environment variable with the same name.
    The substitution of placeholders is 'safe', which means, that if no variable is found, the placeholder will be unchanged.
    The second example shows a mathematical expression. Those expressions can throw exceptions, when they are invalid.
    The third example shows placeholders and mathematical expressions combined.
    Generally, placeholders are substituted first, expressions are evaluated second.
    The forth example shows how to load contents from a file inside the project directory.
    """
    template = Template(gauge_param)
    #pipe operator for sets does not work on windows
    substituted = template.safe_substitute(session_properties())
    template = Template(substituted)
    substituted = template.safe_substitute(os.environ)
    template = Template(substituted)
    substituted = template.safe_substitute(data_store.scenario)
    substituted = _substitute_expressions('#', substituted, lambda expression: array2string(numexpr.evaluate(expression)) )
    substituted = _substitute_expressions('!', substituted, lambda expression: _evaluate_expression(expression))
    return substituted


def _substitute_expressions(marker_char: str, text: str, evaluator: Callable[[str], str]) -> str:
    substituted = text
    while True:
        start = substituted.find(marker_char + '{')
        end = substituted.find('}', start)
        if start < 0 or end < 0:
            break
        expression = substituted[start + 2:end]
        before = substituted[0:start]
        after = substituted[end + 1:len(substituted)]
        value = evaluator(expression)
        substituted = before + value + after
    return substituted


def _evaluate_expression(expression: str) -> str:
    if ":" in expression:
        (cmd, value) = expression.split(':', 1)
    else:
        (cmd, value) = (expression, None)
    cmd = cmd.lower()
    if cmd == "uuid":
        return str(uuid.uuid4())
    elif cmd == "time":
        return _evaluate_time(value)
    elif cmd == "base64":
        return _base64(value)
    elif cmd == "base64urlsafe":
        return _base64_urlsafe(value)
    elif cmd == "base64decode":
        return _base64_decode(value)
    elif cmd == "urlencode":
        return urlcodec.quote_plus(value)
    elif cmd == "urldecode":
        return urlcodec.unquote_plus(value)
    elif cmd == "file":
        return _evaluate_file(value)
    elif cmd in ("gql", "graphql"):
        return _evaluate_gql(value)
    else:
        raise ValueError(f"unsupported substitute {expression}")


def _evaluate_time(format: str) -> str:
    if format is None:
        return datetime.now().isoformat()
    else:
        return datetime.now().strftime(format)


def _base64(text: str) -> str:
    text_bytes = text.encode()
    text_base64_bytes = base64.b64encode(text_bytes)
    return text_base64_bytes.decode()


def _base64_urlsafe(text: str) -> str:
    text_bytes = text.encode()
    text_base64_bytes = base64.urlsafe_b64encode(text_bytes)
    return text_base64_bytes.decode()


def _base64_decode(value: str) -> str:
    """This will decode base64 in standard and URL-safe mode, with or without padding."""
    padding_length = 4 - len(value) % 4
    padding_length = 0 if padding_length == 4 else padding_length
    value = value + padding_length * '='
    value = value.replace('-', '+').replace('_', '/')
    text_bytes = base64.b64decode(value)
    return text_bytes.decode()


def _evaluate_file(file_name: str) -> str:
    file_path = assert_file_is_in_project(file_name)
    with open(file_path, 'r') as f:
        return f.read()


def _evaluate_gql(file_name: str) -> str:
    gql = _evaluate_file(file_name)
    gql_json = json.loads("{}")
    gql_json["query"] = gql
    return json.dumps(gql_json)
