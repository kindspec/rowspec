# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §8: a stored cell whose binary64 value is infinite is
`#REF!(overflow)` wherever an aggregate uses it as an operand (#102).

Both implementations run every case, so a fix in one cannot leave the two
disagreeing.
"""

import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

import rowspec.table as ref  # noqa: E402
import rowspec_alt.table as alt  # noqa: E402

BIG = "9" + "0" * 313  # one beyond binary64
NEAR = "9" + "0" * 307  # just inside it
HUGE = "1" + "0" * 400


def table(values, decl):
    rows = "".join(f"| r_{i} | {v} |\n" for i, v in enumerate(values))
    return f"| id | a |\n| -- | -: |\n{rows}\nkey := id\n{decl}\n"


@pytest.mark.parametrize("impl", [ref, alt], ids=["reference", "rowspec_alt"])
@pytest.mark.parametrize("fn", ["sum", "avg"])
@pytest.mark.parametrize(
    "values",
    [
        # An infinite operand ahead of two finite ones whose partial sum also
        # leaves binary64.
        [BIG, NEAR, NEAR],
        # Two infinities of opposite sign.
        [HUGE, "-" + HUGE],
    ],
    ids=["infinite-among-finite", "opposite-infinities"],
)
def test_an_infinite_operand_makes_the_aggregate_overflow(impl, fn, values):
    _, aggs = impl.evaluate(table(values, f"s := {fn}(a)"))
    assert aggs == {"s": "#REF!(overflow)"}


@pytest.mark.parametrize("impl", [ref, alt], ids=["reference", "rowspec_alt"])
def test_count_does_not_use_an_infinite_cell_as_an_operand(impl):
    """§7: `count` never coerces, so the overflow rule does not reach it."""
    _, aggs = impl.evaluate(table([HUGE, "-" + HUGE], "s := count(a)"))
    assert aggs == {"s": 2}
