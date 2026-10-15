# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A cell is trimmed of ASCII space and tab only, here as everywhere (§4.1.4).

U+00A0 is not trimmed, so a cell holding only one is text, not blank, and
`2<U+00A0>` is text, not the number 2. These pin that for the row-relative
operators and for an order column.

These are unit tests of the two implementations, not conformance cases: the
cases for this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = ["rowspec.table", "rowspec_alt.table"]
N = " "
HEAD = "| id | a | p = prior(a) | d = delta(a) | c = cumulative(a) |\n| -- | -- | -- | -- | -- |\n"
TAIL = "\nkey := id\norder := by(id)\nn := count(p)\n"


def _run(impl, body):
    rows, aggs = importlib.import_module(impl).evaluate(HEAD + body + TAIL)
    return [[str(r[c]) for c in ("p", "d", "c")] for r in rows], str(aggs["n"])


@pytest.mark.parametrize("impl", IMPLS)
def test_an_nbsp_only_cell_is_text_not_blank(impl):
    got, n = _run(impl, f"| r_1 | {N} |  |  |  |\n| r_2 | 1 |  |  |  |\n")
    assert got == [["", "", "#REF!(a)"], ["#REF!(a)", "#REF!(a)", "#REF!(a)"]]
    assert n == "#REF!(a)"


@pytest.mark.parametrize("impl", IMPLS)
def test_a_trailing_nbsp_makes_a_number_text(impl):
    got, _ = _run(impl, f"| r_1 | 1 |  |  |  |\n| r_2 | 2{N} |  |  |  |\n| r_3 | 3 |  |  |  |\n")
    assert got == [
        ["", "", "1.0"],
        ["1.0", "#REF!(a)", "#REF!(a)"],
        ["#REF!(a)", "#REF!(a)", "#REF!(a)"],
    ]


@pytest.mark.parametrize("impl", IMPLS)
def test_an_order_column_of_nbsp_only_cells_is_text_not_blank(impl):
    text = f"| id | o |\n| -- | -- |\n| r_1 | {N} |\n| r_2 | {N} |\n\nkey := id\norder := by(o)\n"
    importlib.import_module(impl).evaluate(text)


@pytest.mark.parametrize("impl", IMPLS)
def test_an_order_number_with_a_trailing_nbsp_mixes_types(impl):
    table = importlib.import_module(impl)
    text = f"| id | o |\n| -- | -- |\n| r_1 | 1 |\n| r_2 | 2{N} |\n\nkey := id\norder := by(o)\n"
    with pytest.raises(table.Malformed) as e:
        table.evaluate(text)
    assert e.value.refusal == "bad-order-column"


@pytest.mark.parametrize("impl", IMPLS)
def test_a_trailing_nbsp_is_part_of_a_text_sort_key(impl):
    # `a` sorts before `a<U+00A0>`; trimmed, the two would tie and the row id
    # would decide, putting r_1 first.
    text = (
        "| id | o | x | p = prior(x) |\n| -- | -- | -- | -- |\n"
        f"| r_1 | a{N} | 1 |  |\n| r_2 | a | 2 |  |\n\nkey := id\norder := by(o)\n"
    )
    rows, _ = importlib.import_module(impl).evaluate(text)
    assert [(r["id"], str(r["p"])) for r in rows] == [("r_2", ""), ("r_1", "2.0")]
