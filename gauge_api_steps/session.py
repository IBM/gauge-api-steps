#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

import os

from getgauge.python import data_store
from .file_util import assert_file_is_in_project


session_changed_key = "_session_changed"
session_file_key = "_session_file"
session_keys_key = "_session_keys"


def load_session_properties(session_file: str) -> None:
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
            store_in_session(key, value, False)


def save_session_properties() -> None:
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


def store_in_session(key: str, value: str, changed: bool=True) -> None:
    data_store.scenario[session_changed_key] = changed
    data_store.scenario[key] = value
    session_keys: list = data_store.scenario.setdefault(session_keys_key, list())
    if key not in session_keys:
        session_keys.append(key)


def session_properties() -> dict:
    session_keys: list = data_store.scenario.setdefault(session_keys_key, list())
    return {key: data_store.scenario.get(key) for key in session_keys}


def _encode_value(value: str) -> str:
    """ this transforms any string into a format, that can be stored in the session properties file. """
    if value is None:
        return None
    return value.encode('unicode_escape').decode()


def _decode_value(value: str) -> str:
    """ decodes a string from the format in the session properties file.  """
    if value is None:
        return None
    return value.encode().decode('unicode_escape')
