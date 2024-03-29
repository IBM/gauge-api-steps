#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import numexpr
import os
import uuid

from datetime import datetime
from getgauge.python import data_store
from numpy import array2string
from string import Template
from typing import Callable
from .file_util import assert_file_is_in_project


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
    file_prefix = "file:"
    expression_lower = expression.lower()
    if expression_lower == "uuid":
        return str(uuid.uuid4())
    elif expression_lower.startswith("time"):
        if expression_lower.startswith("time:"):
            format = expression.split(':', 2)[1]
        elif expression_lower == "time":
            format = None
        else:
            raise ValueError(f"unsupported substitute {expression}")
        if format is None:
            return datetime.now().isoformat()
        else:
            return datetime.now().strftime(format)
    elif expression_lower.startswith(file_prefix):
        file_name = expression[len(file_prefix):]
        file_path = assert_file_is_in_project(file_name)
        with open(file_path, 'r') as f:
            return f.read()
    else:
        raise ValueError(f"unsupported substitute {expression}")
