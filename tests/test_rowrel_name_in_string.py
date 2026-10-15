# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A row-relative name inside a string literal is not an operator (§4.2, §9.9).

`string = DQUOTE *( char - DQUOTE ) DQUOTE` is a value compared against cell
text (§4.2 rule 6), so `"prior(x)"` in a `where` predicate or an `if`
comparison is not a `rowrel-call`. With no `order` declared, §9.9's
`rowrel-without-order` does not apply and the formula is accepted. A real
row-relative call beside such a string is still refused.

Unit tests of the two implementations, not conformance cases: the cases for
this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = pytest.mark.parametrize("impl", ["rowspec.table", "rowspec_alt.table"])

SRC = (
    "| id | n | c | p = {} |\n| -- | -: | -- | -: |\n"
    "| r_1 | 1 | prior(x) |  |\n| r_2 | 2 | y |  |\n\nkey := id\n"
)

IN_STRING = {
    "group-prior": ('sum(n where c = "prior(x)")', ["1.0", "1.0"]),
    "group-delta-open": ('sum(n where c = "delta(")', ["0.0", "0.0"]),
    "group-cumulative": ('count(n where c = "a cumulative(n) b")', ["0", "0"]),
    "if-prior": ('if(c = "prior(x)", 1, 2)', ["1.0", "2.0"]),
    "if-cumulative": ('if(c <> "cumulative(x)", 1, 2)', ["1.0", "1.0"]),
}


@IMPLS
@pytest.mark.parametrize("formula,want", list(IN_STRING.values()), ids=list(IN_STRING))
def test_a_row_relative_name_in_a_string_needs_no_order(impl, formula, want):
    rows, _ = importlib.import_module(impl).evaluate(SRC.format(formula))
    assert [str(r["p"]) for r in rows] == want


@IMPLS
def test_a_row_relative_call_is_still_refused_without_an_order(impl):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate(SRC.format("prior(n)"))
    assert e.value.refusal == "rowrel-without-order"
