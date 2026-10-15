# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A blank value in the key column is not an ident, so it is §9.16 (#111).

These are unit tests of the two implementations, not conformance cases: the
cases for this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = ["rowspec.table", "rowspec_alt.table"]

ONE_BLANK = "| id | a |\n| -- | -: |\n|  | 1 |\n| r_2 | 2 |\n\nkey := id\ns := sum(a)\n"
TWO_BLANKS = "| id | a |\n| -- | -: |\n|  | 1 |\n|  | 2 |\n\nkey := id\ns := sum(a)\n"


@pytest.mark.parametrize("impl", IMPLS)
@pytest.mark.parametrize("text", [ONE_BLANK, TWO_BLANKS], ids=["one-blank", "two-blanks"])
def test_a_blank_key_value_is_bad_identifier(impl, text):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate(text)
    assert e.value.refusal == "bad-identifier"
