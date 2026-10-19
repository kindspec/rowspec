# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A CSV field longer than the csv module's default limit of 131,072
characters is checked like any other (#235).

SPEC.md §9: "Recognition is total" and "This list is complete". No refusal
covers a long field, and §13 takes record boundaries from RFC 4180, which
sets no length limit. So CSV mode lifts the reader's limit rather than
refusing, and it used to crash with `_csv.Error`.

Unit tests of `rowspec.csvmode`, not conformance cases: the cases for this rule
come from an author who has not read `reference/`.
"""

import csv
import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import cli  # noqa: E402
from rowspec.csvmode import check_file, check_text  # noqa: E402
from rowspec.table import Malformed  # noqa: E402

BIG = "x" * 200_000


def write(tmp_path, data):
    p = tmp_path / "t.csv"
    p.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
    return str(p)


def test_a_long_field_is_accepted(tmp_path):
    assert check_file(write(tmp_path, f"id,v\n1,{BIG}\n2,b\n")) == []


def test_a_long_quoted_field_is_accepted(tmp_path):
    assert check_file(write(tmp_path, f'id,v\n1,"{BIG}\nmore"\n')) == []


def test_a_long_field_does_not_hide_a_later_refusal(tmp_path):
    findings = check_file(write(tmp_path, f"id,v\n1,{BIG}\n2,b,c\n"))
    assert [f.rule for f in findings] == ["field-count"]
    assert findings[0].message.startswith("row id='2' has 3 field(s)")


def test_a_long_field_holding_a_stray_quote_names_its_row(tmp_path):
    findings = check_file(write(tmp_path, f'id,v\n1,{BIG}"b\n'))
    assert [f.rule for f in findings] == ["stray-quote"]
    assert findings[0].message.startswith("row id='1': the field 'xxx"), findings[0].message


def test_a_long_field_with_a_byte_that_is_not_utf8_names_the_row(tmp_path):
    with pytest.raises(Malformed) as e:
        check_file(write(tmp_path, f"id,v\n1,{BIG}".encode() + b"\xff\n"))
    assert str(e.value).startswith("row id='1': the field "), str(e.value)


def test_check_text_accepts_a_long_field():
    assert check_text(f"id,v\n1,{BIG}\n") == []


def test_the_cli_checks_it(tmp_path, capsys):
    write(tmp_path, f"id,v\n1,{BIG}\n")
    assert cli.main(["check", str(tmp_path)]) == 0


def test_the_csv_modules_limit_is_put_back(tmp_path):
    # Set a known limit first: a call that leaked the lifted one would
    # otherwise compare it with itself.
    old = csv.field_size_limit(131_072)
    try:
        check_file(write(tmp_path, f"id,v\n1,{BIG}\n"))
        assert csv.field_size_limit() == 131_072
        check_text(f"id,v\n1,{BIG}\n")
        assert csv.field_size_limit() == 131_072
    finally:
        csv.field_size_limit(old)
