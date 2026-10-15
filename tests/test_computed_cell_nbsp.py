# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A computed cell holding only a non-ASCII space holds a value (§4.1.4, §5).

§4.1.4 trims a cell of ASCII space and tab and nothing else, so a cell holding
only U+00A0, U+202F or U+2007 is not empty, and in a computed column that is
§9.17's `value-in-computed-cell`. A cell of ASCII space or tab is empty after
the trim and is accepted.

Unit tests of the two implementations, not conformance cases: the cases for
this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = pytest.mark.parametrize("impl", ["rowspec.table", "rowspec_alt.table"])


def _src(cell):
    return f"| id | a | b = a + 1 |\n| -- | -- | -- |\n| r_1 | 1 | {cell} |\n\nkey := id\n"


@IMPLS
@pytest.mark.parametrize("cell", [" ", " ", " "], ids=["nbsp", "nnbsp", "figure"])
def test_a_computed_cell_holding_only_a_unicode_space_is_refused(impl, cell):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate(_src(cell))
    assert e.value.refusal == "value-in-computed-cell"


@IMPLS
@pytest.mark.parametrize("cell", [" ", "\t"], ids=["space", "tab"])
def test_a_computed_cell_of_ascii_space_or_tab_is_empty(impl, cell):
    rows, _ = importlib.import_module(impl).evaluate(_src(cell))
    assert str(rows[0]["b"]) == "2.0"
