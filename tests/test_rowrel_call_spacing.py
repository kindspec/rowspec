# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A row-relative function name touches its `(` (§4.2 rule 4).

`rowrel-call = rowrel-fn "(" *WSP ident *WSP ")"`, and rule 4 recognises the
eight function names only immediately before `(`, with no `WSP` between. So
`p = prior (n)` is not a row-relative call: read as an `expr`, it is an
`ident` followed by `(`, which `expr` does not generate, and the header cell
is `malformed-formula` (§9.20). It is not `prior(n)`, and with no declared
order it is not `rowrel-without-order` either, since there is no row-relative
operator in it.

Unit tests of the two implementations, not conformance cases: the cases for
this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = pytest.mark.parametrize("impl", ["rowspec.table", "rowspec_alt.table"])

ORDERED = (
    "| id | n | p = {} |\n| -- | -: | -: |\n| r_1 | 1 |  |\n| r_2 | 2 |  |\n\n"
    "key := id\norder := by(id)\n"
)
UNORDERED = "| id | n | p = {} |\n| -- | -: | -: |\n| r_1 | 1 |  |\n| r_2 | 2 |  |\n\nkey := id\n"

SPACED = {
    "prior-space": "prior (n)",
    "delta-tab": "delta\t(n)",
    "cumulative-space": "cumulative (n)",
    "prior-two-spaces": "prior  (n)",
    "delta-space-tab": "delta \t(n)",
    "padded": " cumulative ( n ) ",
}


@IMPLS
@pytest.mark.parametrize("formula", list(SPACED.values()), ids=list(SPACED))
def test_wsp_before_the_paren_is_a_malformed_formula(impl, formula):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate(ORDERED.format(formula))
    assert e.value.refusal == "malformed-formula"


@IMPLS
@pytest.mark.parametrize("formula", list(SPACED.values()), ids=list(SPACED))
def test_wsp_before_the_paren_is_not_a_row_relative_operator(impl, formula):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate(UNORDERED.format(formula))
    assert e.value.refusal == "malformed-formula"


@IMPLS
@pytest.mark.parametrize(
    "formula,want",
    [("prior(n)", ["", "1.0"]), ("delta( n )", ["", "1.0"]), (" cumulative(n) ", ["1.0", "3.0"])],
)
def test_a_touching_paren_is_still_a_row_relative_call(impl, formula, want):
    rows, _ = importlib.import_module(impl).evaluate(ORDERED.format(formula))
    assert [str(r["p"]) for r in rows] == want


@IMPLS
def test_a_touching_paren_without_an_order_is_still_rowrel_without_order(impl):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate(UNORDERED.format("prior(n)"))
    assert e.value.refusal == "rowrel-without-order"
