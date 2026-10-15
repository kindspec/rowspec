# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`prior(c)` over a stored text cell is `#REF!(c)`, not the text (#114).

SPEC.md §4.2 rule 10 leaves a computed value two kinds, a number and an
error, and §8 makes a value that will not coerce `#REF!`. Blank is the one
non-number §7 lets `prior` carry.

These are unit tests of the two implementations, not conformance cases: the
cases for this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = ["rowspec.table", "rowspec_alt.table"]

TEXT = (
    "| id | a | p = prior(a) |\n| -- | -- | -- |\n"
    "| r_1 | x |  |\n| r_2 | y |  |\n| r_3 |  |  |\n| r_4 | 4 |  |\n\n"
    "key := id\norder := by(id)\nn := count(p)\n"
)


@pytest.mark.parametrize("impl", IMPLS)
def test_prior_over_text_is_ref_and_poisons_count(impl):
    rows, aggs = importlib.import_module(impl).evaluate(TEXT)
    got = [str(r["p"]) for r in rows]
    # r_2 follows text, r_3 follows text, r_4 follows a blank.
    assert got == ["", "#REF!(a)", "#REF!(a)", ""]
    assert str(aggs["n"]) == "#REF!(a)"
