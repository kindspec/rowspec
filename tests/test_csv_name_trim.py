# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §13: a CSV column name is trimmed of ASCII space and tab only, as a
key value is (§4.1.4), before §9.2 compares names (#118).

Unit tests of `rowspec.csvmode`, not conformance cases: the cases for this rule
come from an author who has not read `reference/`.
"""

import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import csvmode  # noqa: E402


def duplicate(header):
    findings = csvmode.check_text(header + "\nr1,1,2\n")
    return any(f.rule == "duplicate-column" for f in findings)


@pytest.mark.parametrize(
    "header",
    ["id, ,", "id,\t,", "id,a, a ", "id,a,\ta\t"],
    ids=["space-and-empty", "tab-and-empty", "padded-with-spaces", "padded-with-tabs"],
)
def test_names_equal_after_trimming_ascii_space_and_tab_are_duplicates(header):
    assert duplicate(header)


@pytest.mark.parametrize(
    "header",
    ["id,a,a ", "id, ,", "id,a, a", "id,　,"],
    ids=["nbsp-after", "nbsp-and-empty", "figure-space-before", "ideographic-space-and-empty"],
)
def test_a_non_ascii_space_at_the_edge_of_a_name_is_part_of_it(header):
    assert not duplicate(header)
