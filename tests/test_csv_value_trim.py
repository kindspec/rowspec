# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §13: CSV mode trims a key, order or typed column value of ASCII
space and tab only (§4.1.4), so a leading or trailing U+00A0 is part of the
value (#145).

Unit tests of the reference implementation, not conformance cases: the cases
for this rule come from an author who has not read `reference/`.
"""

import json
import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec.csvmode import check_file  # noqa: E402

SPACES = pytest.mark.parametrize(
    "sp", ["\u00a0", "\u2003", "\u202f"], ids=["nbsp", "em", "narrow-nbsp"]
)


def check(tmp_path, body, side):
    p = tmp_path / "t.csv"
    p.write_text(body, encoding="utf-8")
    (tmp_path / "t.csv.rowspec.json").write_text(json.dumps(side), encoding="utf-8")
    return check_file(str(p))


def rules(findings):
    return sorted({f.rule for f in findings})


@SPACES
def test_an_order_value_padded_with_a_unicode_space_is_text(tmp_path, sp):
    found = check(tmp_path, f"id,o\nr1,{sp}5\nr2,6\n", {"key": "id", "order": "o"})
    assert rules(found) == ["order-mixed-types"]


@SPACES
def test_a_number_column_value_padded_with_a_unicode_space_is_not_a_number(tmp_path, sp):
    side = {"key": "id", "columns": {"n": "number"}}
    found = check(tmp_path, f"id,n\nr1,{sp}5\nr2,6\n", side)
    assert rules(found) == ["column-type"]


@SPACES
def test_a_key_value_padded_with_a_unicode_space_is_not_a_duplicate(tmp_path, sp):
    found = check(tmp_path, f"id,n\na,1\na{sp},2\n", {"key": "id"})
    assert rules(found) == ["key-not-identifier"]
    # The finding names the row by its own value, not by the row `a`.
    assert f"row id='a{sp}'" in str(found[0])


@pytest.mark.parametrize(
    "body, side, want",
    [
        ("id,o\nr1,\t5 \nr2,6\n", {"key": "id", "order": "o"}, []),
        ("id,n\nr1, 5\t\nr2,6\n", {"key": "id", "columns": {"n": "number"}}, []),
        ("id,n\na,1\na \t,2\n", {"key": "id"}, ["duplicate-key"]),
    ],
    ids=["order", "number", "key"],
)
def test_ascii_space_and_tab_are_trimmed(tmp_path, body, side, want):
    """The same values padded with ASCII space and tab are trimmed, so the
    findings above are about the character and not about padding."""
    assert rules(check(tmp_path, body, side)) == want
