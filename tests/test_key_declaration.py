# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`key := col` names a stored column of the table, or it is §9.12 (#100).

These are unit tests of the two implementations, not conformance cases: the
cases for this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = ["rowspec.table", "rowspec_alt.table"]

MISSING = "| id | a |\n| -- | -: |\n| r_1 | 1 |\n\nkey := nope\n"
COMPUTED = "| id | a | b = a * 2 |\n| -- | -: | -: |\n| r_1 | 1 |  |\n\nkey := b\n"
STORED = "| id | a | b = a * 2 |\n| -- | -: | -: |\n| r_1 | 1 |  |\n\nkey := id\n"


@pytest.mark.parametrize("impl", IMPLS)
@pytest.mark.parametrize(
    ("text", "column"), [(MISSING, "nope"), (COMPUTED, "b")], ids=["missing", "computed"]
)
def test_a_key_naming_no_stored_column_is_malformed_declaration(impl, text, column):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate(text)
    assert e.value.refusal == "malformed-declaration"
    assert column in str(e.value)


@pytest.mark.parametrize("impl", IMPLS)
def test_a_key_naming_a_stored_column_is_accepted(impl):
    importlib.import_module(impl).evaluate(STORED)
