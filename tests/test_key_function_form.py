# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`key := fn(col)` is §9.12 `malformed-declaration`, whatever `fn` is (#110).

These are unit tests of the two implementations, not conformance cases: the
cases for this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = ["rowspec.table", "rowspec_alt.table"]

TABLE = "| id | g |\n| -- | -- |\n| r_1 | a |\n\n"


@pytest.mark.parametrize("impl", IMPLS)
@pytest.mark.parametrize(
    "decl",
    [
        "key := by(id)",
        "key := sum(id)",
        "key:=by(id)",
        "key := by( id )",
        "key := by(id) # note",
        'key := sum(id where g = "a")',
    ],
)
def test_a_key_in_function_form_is_malformed_declaration(impl, decl):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate(TABLE + decl + "\n")
    assert e.value.refusal == "malformed-declaration"


@pytest.mark.parametrize("impl", IMPLS)
def test_a_bare_key_is_accepted(impl):
    importlib.import_module(impl).evaluate(TABLE + "key := id\n")
