# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §13: a sidecar's order column is refused when it is blank in any
row, a cell of spaces or tabs included (§6, §9.10; #180).

Unit tests of `rowspec.csvmode`, not conformance cases: the cases for this rule
come from an author who has not read `reference/`.
"""

import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import sidecar  # noqa: E402
from rowspec.csvmode import check_text  # noqa: E402

ORDER = sidecar.Sidecar("t.csv.rowspec.json", key="id", order="n")


def rules(text, side=ORDER):
    return sorted({f.rule for f in check_text(text, "t.csv", side)})


@pytest.mark.parametrize(
    "cell",
    ["", " ", "\t", " \t ", '"  "', '""'],
    ids=["empty", "space", "tab", "spaces-and-tab", "quoted-spaces", "quoted-empty"],
)
def test_a_blank_order_cell_is_refused(cell):
    assert rules(f"id,n\na,1\nb,{cell}\n") == ["order-blank"]


def test_a_blank_order_cell_is_refused_in_the_first_row():
    assert rules("id,n\na,\nb,2\n") == ["order-blank"]


def test_a_column_of_only_blanks_is_refused():
    assert rules("id,n\na,\nb, \n") == ["order-blank"]


def test_the_blank_row_is_named_by_its_key():
    found = check_text("id,n\na,1\nb,\n", "t.csv", ORDER)
    assert [str(f) for f in found] == ["order column 'n' is blank at row id='b'"]


def test_a_non_ascii_space_is_not_blank_but_text():
    # §4.1.4 trims ASCII space and tab only, so U+00A0 is a text value.
    assert rules("id,n\na,1\nb,\u00a0\n") == ["order-mixed-types"]
    assert rules("id,n\na,x\nb,\u00a0\n") == []


def test_a_file_with_no_data_rows_is_not_refused_on_order():
    assert rules("id,n\n") == []


def test_a_blank_in_a_column_that_is_not_the_order_column_is_not_refused():
    assert rules("id,n,m\na,1,\nb,2, \n") == []
