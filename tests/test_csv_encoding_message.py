# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Bytes that are not UTF-8 are refused by entity, never by offset (#216).

A CSV names the row as every other CSV-mode finding does: by the declared
key, else the first field, else the record number, or the header row. It
quotes the field holding the byte, spelled `\\xNN`. A sidecar quotes the
line holding it.

Unit tests of `rowspec.csvmode` and `rowspec.sidecar`, not conformance
cases: the cases for this rule come from an author who has not read
`reference/`.
"""

import json
import os
import re
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec.csvmode import check_file  # noqa: E402
from rowspec.table import Malformed  # noqa: E402


def refusal(tmp_path, data, sidecar=None, sidecar_bytes=None):
    p = tmp_path / "t.csv"
    p.write_bytes(data)
    if sidecar is not None:
        (tmp_path / "t.csv.rowspec.json").write_text(json.dumps(sidecar))
    if sidecar_bytes is not None:
        (tmp_path / "t.csv.rowspec.json").write_bytes(sidecar_bytes)
    with pytest.raises(Malformed) as e:
        check_file(str(p))
    return str(e.value)


#: An offset in any spelling: `byte 0xE9` is the byte, `byte 14` would be where.
NO_OFFSET = re.compile(r"offset|position|\bat \d|\bline \d|\bbyte \d+\b")


@pytest.mark.parametrize(
    "data, sidecar, where",
    [
        (b"id,v\n1,a\n2,caf\xe9\n", None, "row id='2': the field 'caf\\xe9'"),
        (b"id,v\n1,a\n2,caf\xe9\n", {"key": "v"}, "row v='caf\\xe9': the field 'caf\\xe9'"),
        (b"id,caf\xe9\n1,a\n", None, "the header row: the field 'caf\\xe9'"),
        (b"id,v\n,x\xff\n", None, "record 1: the field 'x\\xff'"),
        (b'id,v\nr1,a\nr2,"two\nlines \xff"\n', None, "row id='r2': the field 'two\\nlines \\xff'"),
        (b"\xef\xbb\xbfid;v\nr1;x\xc3\n", {"delimiter": ";"}, "row id='r1': the field 'x\\xc3'"),
    ],
    ids=[
        "first-field",
        "declared-key",
        "header",
        "record-number",
        "multi-line",
        "bom-and-delimiter",
    ],
)
def test_a_csv_names_the_row_and_field(tmp_path, data, sidecar, where):
    msg = refusal(tmp_path, data, sidecar)
    assert msg.startswith(f"{where} is not valid UTF-8: byte 0x"), msg
    assert "is not part of a valid sequence" in msg
    assert not NO_OFFSET.search(msg), msg


def test_a_csv_message_names_the_first_bad_byte(tmp_path):
    msg = refusal(tmp_path, b"id,v\nr1,ok\nr2,\xe9\xff\nr3,\xfe\n")
    assert msg.startswith("row id='r2': the field '\\xe9\\xff' is not valid UTF-8: byte 0xE9 "), msg


def test_a_sidecar_quotes_the_line(tmp_path):
    msg = refusal(tmp_path, b"id,v\n1,a\n", sidecar_bytes=b'{\n  "key": "caf\xe9"\n}\n')
    assert msg == (
        't.csv.rowspec.json is not valid UTF-8: the line \'  "key": "caf\\xe9"\' holds '
        "byte 0xE9, which is not part of a valid sequence (invalid continuation byte)"
    ), msg


def test_a_long_sidecar_line_is_shown_around_the_byte(tmp_path):
    side = b'{"key":"id","order":"v","columns":{"population":"number","caf\xe9":"text"}}'
    msg = refusal(tmp_path, b"id,v\n1,a\n", sidecar_bytes=side)
    assert "caf\\xe9" in msg, msg
    assert not NO_OFFSET.search(msg), msg


def test_a_long_csv_field_is_shown_around_the_byte(tmp_path):
    msg = refusal(tmp_path, b"id,v\n1," + b"x" * 80 + b"\xff\n")
    assert msg.startswith("row id='1': the field '…xxxxxxxxxx\\xff' is not valid UTF-8"), msg


def test_a_field_too_large_for_the_csv_module_names_the_file(tmp_path):
    msg = refusal(tmp_path, b"id,v\n1," + b"x" * 200_000 + b"\xff\n")
    assert msg == (
        "the file is not valid UTF-8: byte 0xFF is not part of a valid sequence "
        "(invalid start byte)"
    ), msg


def test_the_first_of_two_bad_fields_in_a_record_is_named(tmp_path):
    msg = refusal(tmp_path, b"id,a,b\nr1,x\xe9,y\xff\n")
    assert msg.startswith("row id='r1': the field 'x\\xe9' is not valid UTF-8: byte 0xE9 "), msg


def test_a_crlf_sidecar_line_is_quoted_without_its_cr(tmp_path):
    msg = refusal(tmp_path, b"id,v\n1,a\n", sidecar_bytes=b'{\r\n  "key": "caf\xe9"\r\n}\r\n')
    assert 'the line \'  "key": "caf\\xe9"\' holds byte 0xE9' in msg, msg
