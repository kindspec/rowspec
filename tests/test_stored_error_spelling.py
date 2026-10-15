# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A stored cell spelled like an error value is text, not that error (#126).

SPEC.md §4.1 rule 6: a cell that does not match `number` is text, `#REF!`
when used as an arithmetic or aggregate operand -- `#REF!(c)` for its own
column, per §8. §7: `count` counts rows and is poisoned only by an error
actually present, which stored text is not.

These are unit tests of the two implementations, not conformance cases: the
cases for this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = ["rowspec.table", "rowspec_alt.table"]

TABLE = (
    "| id | g | a | x = a + 1 | t = sum(a where g = @g) | c = count(a where g = @g) |\n"
    "| -- | -- | -- | -- | -- | -- |\n"
    "| r_1 | A | 1 |  |  |  |\n"
    "| r_2 | A | #REF!(zz) |  |  |  |\n\n"
    "key := id\ns := sum(a)\nn := count(a)\n"
)


@pytest.mark.parametrize("impl", IMPLS)
def test_a_stored_error_spelling_is_text(impl):
    rows, aggs = importlib.import_module(impl).evaluate(TABLE)
    assert str(aggs["s"]) == "#REF!(a)"
    assert str(aggs["n"]) == "2"
    r_1, r_2 = rows
    assert str(r_2["x"]) == "#REF!(a)"
    assert str(r_1["t"]) == "#REF!(a)"
    assert str(r_1["c"]) == "2"


PRIOR = (
    "| id | a | p = prior(a) |\n| -- | -- | -- |\n"
    "| r_1 | #REF!(zz) |  |\n| r_2 | 1 |  |\n| r_3 | 2 |  |\n\n"
    "key := id\norder := by(id)\nn := count(p)\ns := sum(p)\n"
)


@pytest.mark.parametrize("impl", IMPLS)
def test_prior_over_a_stored_error_spelling_is_ref_of_its_column(impl):
    rows, aggs = importlib.import_module(impl).evaluate(PRIOR)
    assert [str(r["p"]) for r in rows] == ["", "#REF!(a)", "1.0"]
    assert str(aggs["n"]) == "#REF!(a)"
    assert str(aggs["s"]) == "#REF!(a)"


BIG = "1" + "0" * 400  # finite as written, infinite as binary64: #REF!(overflow)


@pytest.mark.parametrize("impl", IMPLS)
@pytest.mark.parametrize("first", ["big", "text"])
def test_a_stored_overflow_spelling_is_text_beside_a_real_overflow(impl, first):
    # §8 ranks #REF!(a) ahead of #REF!(overflow). The text cell must count as
    # text in either row order, never as the overflow it is spelled like.
    cells = [BIG, "#REF!(overflow)"] if first == "big" else ["#REF!(overflow)", BIG]
    text = (
        "| id | a |\n| -- | -- |\n"
        + "".join(f"| r_{i} | {c} |\n" for i, c in enumerate(cells))
        + "\nkey := id\ns := sum(a)\nn := count(a)\n"
    )
    aggs = importlib.import_module(impl).evaluate(text)[1]
    assert str(aggs["s"]) == "#REF!(a)"
    assert str(aggs["n"]) == "2"
