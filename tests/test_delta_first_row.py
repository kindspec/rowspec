# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §7: in the first row of the declared order, `delta(c)` is blank
only when `c` is a number there, and otherwise carries the error `c` gives
(#142).

Unit tests of the two implementations, not conformance cases: the cases for
this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = pytest.mark.parametrize("impl", ["rowspec.table", "rowspec_alt.table"])

BIG = "1" + "0" * 400  # beyond binary64


def first(impl, a, formula="c = a"):
    # `r_1` sorts first, so the first row is not the first line of the file.
    src = (
        f"| id | a | {formula} | d = delta(c) |\n| -- | -: | -: | -: |\n"
        f"| r_2 | 1 |  |  |\n| r_1 | {a} |  |  |\n"
        "\nkey := id\norder := by(id)\n"
    )
    rows, _ = importlib.import_module(impl).evaluate(src)
    return {r["id"]: str(r["d"]) for r in rows}


@IMPLS
@pytest.mark.parametrize(
    "a, formula, want",
    [
        ("5", "c = a", ""),
        ("1", "c = a / 0", "#REF!(/0)"),
        ("1", "c = nope + a", "#REF!(nope)"),
        ("", "c = a + 0", "#REF!(a)"),
        (BIG, "c = a + 0", "#REF!(overflow)"),
    ],
    ids=["number", "div-by-zero", "unresolved-name", "blank-operand", "overflow"],
)
def test_delta_in_the_first_row_over_a_computed_column(impl, a, formula, want):
    assert first(impl, a, formula)["r_1"] == want


def stored_first(impl, a):
    src = (
        "| id | a | d = delta(a) |\n| -- | -: | -: |\n"
        f"| r_1 | {a} |  |\n| r_2 | 3 |  |\n"
        "\nkey := id\norder := by(id)\n"
    )
    rows, _ = importlib.import_module(impl).evaluate(src)
    return str(rows[0]["d"])


@IMPLS
@pytest.mark.parametrize(
    "a, want",
    [("5", ""), ("", "#REF!(a)"), ("x", "#REF!(a)"), (BIG, "#REF!(overflow)")],
    ids=["number", "blank", "text", "overflow"],
)
def test_delta_in_the_first_row_over_a_stored_column(impl, a, want):
    assert stored_first(impl, a) == want
