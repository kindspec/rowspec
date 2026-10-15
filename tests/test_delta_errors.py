# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §7: `delta(c)` is `c - prior(c)`, so when this row and the
preceding row both give a `#REF!`, §8's leftmost rule picks this row's (#116).

Unit tests of the two implementations, not conformance cases: the cases for
this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = pytest.mark.parametrize("impl", ["rowspec.table", "rowspec_alt.table"])

BIG = "1" + "0" * 400  # beyond binary64
OVF = "#REF!(overflow)"
ORDER = "\nkey := id\norder := by(id)\n"


def stored(impl, prev, cur):
    src = (
        "| id | a | d = delta(a) |\n| -- | -: | -: |\n"
        f"| r_1 | {prev} |  |\n| r_2 | {cur} |  |\n" + ORDER
    )
    rows, _ = importlib.import_module(impl).evaluate(src)
    return rows[1]["d"]


@IMPLS
@pytest.mark.parametrize(
    "prev, cur, want",
    [
        (BIG, "", "#REF!(a)"),
        ("", BIG, OVF),
        (BIG, "x", "#REF!(a)"),
        ("x", BIG, OVF),
    ],
    ids=[
        "blank-after-overflow",
        "overflow-after-blank",
        "text-after-overflow",
        "overflow-after-text",
    ],
)
def test_delta_carries_this_rows_error_over_a_stored_column(impl, prev, cur, want):
    assert str(stored(impl, prev, cur)) == want


# `c = a / z`: (a, z) gives c's value in a row.
SHAPES = {"/0": ("1", "0"), "blank": ("", "1"), "overflow": (BIG, "1")}


def computed(impl, prev, cur):
    (pa, pz), (ca, cz) = SHAPES[prev], SHAPES[cur]
    src = (
        "| id | a | z | c = a / z | d = delta(c) |\n| -- | -: | -: | -: | -: |\n"
        f"| r_1 | {pa} | {pz} |  |  |\n| r_2 | {ca} | {cz} |  |  |\n" + ORDER
    )
    rows, _ = importlib.import_module(impl).evaluate(src)
    return rows[1]["d"]


@IMPLS
@pytest.mark.parametrize(
    "prev, cur, want",
    [
        ("overflow", "/0", "#REF!(/0)"),
        ("/0", "overflow", OVF),
        ("/0", "blank", "#REF!(a)"),
        ("blank", "/0", "#REF!(/0)"),
    ],
)
def test_delta_carries_this_rows_own_error_over_a_computed_column(impl, prev, cur, want):
    """The error this row's `c` originated, not a relabelled `#REF!(c)` (§8)."""
    assert str(computed(impl, prev, cur)) == want
