# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §13: a sidecar `delimiter` is one Unicode scalar value other than
`"`, CR or LF, and anything else is refused (#178).

Unit tests of `rowspec.csvmode`, not conformance cases: the cases for this rule
come from an author who has not read `reference/`.
"""

import json
import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import cli  # noqa: E402
from rowspec.csvmode import check_file  # noqa: E402
from rowspec.table import Malformed  # noqa: E402


def write(tmp_path, data, sidecar_json):
    p = tmp_path / "t.csv"
    p.write_bytes(data)
    (tmp_path / "t.csv.rowspec.json").write_text(sidecar_json, encoding="utf-8")
    return str(p)


# Each is the JSON text of the member's value, so the escapes reach the parser.
RESERVED = {"double-quote": r'"\""', "cr": r'"\r"', "lf": r'"\n"'}


@pytest.mark.parametrize("value", RESERVED.values(), ids=RESERVED.keys())
def test_a_delimiter_rfc_4180_reserves_is_refused(tmp_path, value):
    p = write(tmp_path, b"id,n\na,1\n", '{"delimiter": ' + value + "}")
    with pytest.raises(Malformed, match="reserved"):
        check_file(p)


@pytest.mark.parametrize("value", RESERVED.values(), ids=RESERVED.keys())
def test_a_reserved_delimiter_is_a_refusal_on_the_cli(tmp_path, capsys, value):
    write(tmp_path, b"id,n\na,1\n", '{"delimiter": ' + value + "}")
    assert cli.main(["check", str(tmp_path)]) == 1


@pytest.mark.parametrize("value", [r'"\ud800"', r'"\udfff"'], ids=["high", "low"])
def test_a_lone_surrogate_is_not_a_scalar_value_and_is_refused(tmp_path, value):
    p = write(tmp_path, b"id,n\na,1\n", '{"delimiter": ' + value + "}")
    with pytest.raises(Malformed, match="one Unicode scalar value"):
        check_file(p)


@pytest.mark.parametrize(
    "delimiter",
    [";", "\t", " ", "\U0001f600", "\ufeff"],
    ids=["semicolon", "tab", "space", "astral", "bom-character"],
)
def test_any_other_scalar_value_is_a_delimiter(tmp_path, delimiter):
    data = f"id{delimiter}n\na{delimiter}1\na{delimiter}2\n".encode()
    p = write(tmp_path, data, json.dumps({"key": "id", "delimiter": delimiter}))
    assert {f.rule for f in check_file(p)} == {"duplicate-key"}
