# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §4.1.6 and §4.1.7 in CSV mode: a value is a number only if it
matches `number`, and a date only if it matches `date`, with `DIGIT` ASCII
only and one separator per date (#155). These decide a typed column's check
and an order column's type (§9.10).

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

NUMBER = {"key": "id", "columns": {"n": "number"}}
DATE = {"key": "id", "columns": {"n": "date"}}
ORDER = {"key": "id", "order": "n"}


def check(tmp_path, value, side, other):
    """`value` in row r1 and `other` in row r2 of column `n`. The value is
    quoted, so it may hold a line break."""
    v = value.replace('"', '""')
    p = tmp_path / "t.csv"
    p.write_text(f'id,n\nr1,"{v}"\nr2,{other}\n', encoding="utf-8")
    (tmp_path / "t.csv.rowspec.json").write_text(json.dumps(side), encoding="utf-8")
    return check_file(str(p))


def rules(findings):
    return sorted({f.rule for f in findings})


NOT_NUMBERS = pytest.mark.parametrize(
    "value",
    ["+5", "1e3", "1E3", "5e-1", ".5", "5.", "-.5", "\u0665", "1\u0665", "\uff15", "5\n"],
    ids=[
        "plus",
        "exponent",
        "upper-exponent",
        "negative-exponent",
        "leading-point",
        "trailing-point",
        "negative-leading-point",
        "arabic-indic-five",
        "mixed-digit-families",
        "fullwidth-five",
        "trailing-lf",
    ],
)

NOT_DATES = pytest.mark.parametrize(
    "value",
    [
        "2024-01/05",
        "2024/01-05",
        "\u0662\u0660\u0662\u0664-01-05",
        "2024-\u0660\u0661-05",
        "2024-01-05\n",
        "12024-01-05",
        "2024-001-05",
    ],
    ids=[
        "hyphen-then-slash",
        "slash-then-hyphen",
        "arabic-indic-year",
        "arabic-indic-month",
        "trailing-lf",
        "five-digit-year",
        "three-digit-month",
    ],
)


@NOT_NUMBERS
def test_a_number_column_refuses_what_number_does_not_match(tmp_path, value):
    assert rules(check(tmp_path, value, NUMBER, "6")) == ["column-type"]


@pytest.mark.parametrize("value", ["5", "-5", "007", "1.50", "-0.25"])
def test_a_number_column_accepts_what_number_matches(tmp_path, value):
    """Controls: `007` and `1.50` are admitted by §4.1.6, so the refusals
    above are about the spellings it lists and not about any digit string."""
    assert check(tmp_path, value, NUMBER, "6") == []


@NOT_DATES
def test_a_date_column_refuses_what_date_does_not_match(tmp_path, value):
    assert rules(check(tmp_path, value, DATE, "2024-01-06")) == ["column-type"]


@pytest.mark.parametrize("value", ["2024-01-05", "2024/1/5", "1-2-3", "2024-13-45"])
def test_a_date_column_accepts_what_date_matches(tmp_path, value):
    """Controls: either separator, used twice, and no calendar validation."""
    assert check(tmp_path, value, DATE, "2024-01-06") == []


@NOT_NUMBERS
def test_an_order_value_that_is_not_a_number_is_text_beside_a_number(tmp_path, value):
    """§9.10: the value is text, so the column mixes types. Only that is
    reported: `1e3` is not a non-finite number either, it is not a number."""
    assert rules(check(tmp_path, value, ORDER, "6")) == ["order-mixed-types"]


@NOT_DATES
def test_an_order_value_that_is_not_a_date_is_text_beside_a_date(tmp_path, value):
    assert rules(check(tmp_path, value, ORDER, "2024-01-06")) == ["order-mixed-types"]


def test_an_exponent_beyond_binary64_is_text_not_a_non_finite_number(tmp_path):
    """`1e999` is text by §4.1.6, so the order column mixes types, and the
    non-finite check, which is about numbers, does not fire on it."""
    assert rules(check(tmp_path, "1e999", ORDER, "6")) == ["order-mixed-types"]


def test_a_number_beyond_binary64_in_an_order_column_is_still_non_finite(tmp_path):
    """A digit string too long for binary64 matches `number`, so it is a
    number and the non-finite check still sees it."""
    assert rules(check(tmp_path, "9" * 400, ORDER, "6")) == ["order-non-finite"]
