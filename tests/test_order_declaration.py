# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`order` has one form, `order := by(c)`, and `c` is a stored column (#202).

§4.1.11 and §9.12 refuse any other `order` construct as a malformed
declaration, a `where` form included; §9.10 refuses `by(c)` naming no column
whatever the row count.

These are unit tests of the two implementations, not conformance cases: the
cases for this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = ["rowspec.table", "rowspec_alt.table"]

HEAD = "| id | a |\n| -- | -- |\n"
ROW = "| r_1 | 1 |\n"


@pytest.mark.parametrize("impl", IMPLS)
@pytest.mark.parametrize(
    "rhs",
    ['count(a where a = "1")', 'by(a where a = "1")'],
    ids=["aggregate-where", "by-where"],
)
def test_an_order_with_a_where_is_malformed_declaration(impl, rhs):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate(f"{HEAD}{ROW}\nkey := id\norder := {rhs}\n")
    assert e.value.refusal == "malformed-declaration"


@pytest.mark.parametrize("impl", IMPLS)
@pytest.mark.parametrize("rows", ["", ROW], ids=["no-rows", "one-row"])
def test_an_order_naming_no_column_is_bad_order_column(impl, rows):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate(f"{HEAD}{rows}\nkey := id\norder := by(n)\n")
    assert e.value.refusal == "bad-order-column"


@pytest.mark.parametrize("impl", IMPLS)
def test_an_order_naming_a_stored_column_of_an_empty_table_is_accepted(impl):
    importlib.import_module(impl).evaluate(f"{HEAD}\nkey := id\norder := by(a)\n")
