# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §9.10: an order column is refused when it holds a non-finite
spelling (`inf`, `nan`, `infinity`, any case, bare or after one leading `+`
or `-`) in any row (#168), including a column of nothing else, where every
value is text and the column has one type.

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

import rowspec.table as ref  # noqa: E402
import rowspec_alt.table as alt  # noqa: E402
from rowspec.csvmode import check_file  # noqa: E402

IMPLS = pytest.mark.parametrize("impl", [ref, alt], ids=["reference", "rowspec_alt"])

SPELLED = pytest.mark.parametrize(
    "cells",
    [
        ["inf", "nan"],
        ["INF", "Infinity"],
        ["nan", "nan2"],
        ["x", "NaN"],
        ["infinity"],
        ["-inf", "+nan"],
        ["-Infinity", "+INF"],
        ["x", "-NaN"],
        ["+infinity"],
    ],
    ids=[
        "inf-nan",
        "upper-and-mixed-case",
        "beside-text",
        "in-a-later-row",
        "one-row",
        "signed",
        "signed-upper-and-mixed-case",
        "signed-in-a-later-row",
        "signed-one-row",
    ],
)

# Text that is not one of the three spellings: a word that starts with one,
# fullwidth letters, which no case mapping turns into ASCII, and signs that are
# not a single leading `+` or `-` directly before the spelling.
NOT_SPELLED = pytest.mark.parametrize(
    "cells",
    [
        ["nanny", "info"],
        ["ｉｎｆ", "x"],
        ["inf x", "y"],
        ["-info", "+nanny"],
        ["--inf", "+-nan"],
        ["- inf", "x"],
        ["inf-", "nan+"],
    ],
    ids=[
        "longer-words",
        "fullwidth",
        "inner-space",
        "signed-longer-words",
        "two-signs",
        "space-after-sign",
        "trailing-sign",
    ],
)


def mdtbl(cells, order="o"):
    rows = "".join(f"| r_{i} | {c} |\n" for i, c in enumerate(cells))
    return f"| id | o |\n| -- | -- |\n{rows}\nkey := id\norder := by({order})\n"


@IMPLS
@SPELLED
def test_an_order_column_holding_a_spelling_is_refused(impl, cells):
    with pytest.raises(impl.Malformed) as ex:
        impl.evaluate(mdtbl(cells))
    assert ex.value.refusal == "bad-order-column"


@IMPLS
@NOT_SPELLED
def test_an_order_column_of_other_text_is_accepted(impl, cells):
    impl.evaluate(mdtbl(cells))


@IMPLS
def test_a_spelling_outside_the_order_column_is_text(impl):
    """Control: §9.10 is about the order column only."""
    src = "| id | o | t |\n| -- | -- | -- |\n| r_0 | 1 | inf |\n| r_1 | 2 | nan |\n"
    impl.evaluate(src + "\nkey := id\norder := by(o)\n")


def csv_rules(tmp_path, cells):
    p = tmp_path / "t.csv"
    p.write_text("id,o,t\n" + "".join(f"r{i},{c},inf\n" for i, c in enumerate(cells)), "utf-8")
    (tmp_path / "t.csv.rowspec.json").write_text(json.dumps({"key": "id", "order": "o"}))
    return sorted({f.rule for f in check_file(str(p))})


@SPELLED
def test_csv_an_order_column_holding_a_spelling_is_refused(tmp_path, cells):
    assert csv_rules(tmp_path, cells) == ["order-non-finite"]


@NOT_SPELLED
def test_csv_an_order_column_of_other_text_is_accepted(tmp_path, cells):
    """Each file also holds `inf` in a column that is not the order column."""
    assert csv_rules(tmp_path, cells) == []


def test_csv_a_spelling_beside_a_number_is_also_mixed_types(tmp_path):
    assert csv_rules(tmp_path, ["nan", "1"]) == ["order-mixed-types", "order-non-finite"]


def test_csv_a_signed_spelling_beside_a_number_is_also_mixed_types(tmp_path):
    assert csv_rules(tmp_path, ["-inf", "1"]) == ["order-mixed-types", "order-non-finite"]
