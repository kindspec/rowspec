# SPDX-License-Identifier: Apache-2.0 OR MIT
"""CSV mode's non-UTF-8 refusal spells a literal backslash `\\\\`, so `\\xNN`
in its quotes is always a byte, and never cuts a `\\xNN` in half (#242)."""

import json
import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec.csvmode import check_file  # noqa: E402
from rowspec.table import Malformed  # noqa: E402


def message(tmp_path, data, sidecar=None):
    p = tmp_path / "a.csv"
    p.write_bytes(data)
    if sidecar is not None:
        (tmp_path / "a.csv.rowspec.json").write_text(json.dumps(sidecar))
    try:
        findings = check_file(str(p))
    except Malformed as e:
        return str(e)
    return " | ".join(str(f) for f in findings)


def test_field_tells_text_from_byte(tmp_path):
    m = message(tmp_path, b"id,v\n1,\\xe9\xe9\n")
    assert "row id='1': the field '\\\\xe9\\xe9' is not valid UTF-8" in m, m


def test_row_name_tells_text_from_byte(tmp_path):
    m = message(tmp_path, b"id,v\n\\xe9\xe9,1\n")
    assert "row id='\\\\xe9\\xe9': the field '\\\\xe9\\xe9'" in m, m


def test_declared_key_tells_text_from_byte(tmp_path):
    m = message(tmp_path, b"v,id\n\xe9,a\\b\n", {"key": "id"})
    assert "row id='a\\\\b': the field '\\xe9'" in m, m


def test_truncation_never_cuts_a_spelled_byte(tmp_path):
    m = message(tmp_path, b"id,v\n1,aaaaaaaaaa" + b"\xe9" * 8 + b"\n")
    assert "the field 'aaaaaaaaaa" + "\\xe9" * 7 + "…'" in m, m


def test_plain_field_is_unchanged(tmp_path):
    m = message(tmp_path, b"id,v\n1,caf\xe9\n")
    assert "row id='1': the field 'caf\\xe9' is not valid UTF-8" in m, m
