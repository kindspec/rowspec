# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Files on which the reference and rowspec_alt used to disagree (#100).

Both implementations run every case, so a fix in one cannot leave the two
disagreeing again.
"""

import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

import rowspec.table as ref  # noqa: E402
import rowspec_alt.table as alt  # noqa: E402

IMPLS = pytest.mark.parametrize("impl", [ref, alt], ids=["reference", "rowspec_alt"])


@IMPLS
@pytest.mark.parametrize(
    "cells",
    [["", ""], ["", "3"]],
    ids=["blank-in-every-row", "blank-in-one-row"],
)
def test_an_order_column_blank_in_any_row_is_refused(impl, cells):
    """SPEC.md §9.10: an order column that "is blank in any row". A column
    blank in every row mixes no types, so only the "blank" wording reaches it."""
    rows = "".join(f"| r_{i} | {c} |\n" for i, c in enumerate(cells))
    src = f"| id | d |\n| -- | -- |\n{rows}\nkey := id\norder := by(d)\n"
    with pytest.raises(impl.Malformed) as ex:
        impl.evaluate(src)
    assert ex.value.refusal == "bad-order-column"


@IMPLS
@pytest.mark.parametrize(
    "formula, want",
    [
        ('sum(nope where a = "x")', "#REF!(nope)"),
        ("sum(nope where a = @a)", "#REF!(nope)"),
        ('count(nope where a = "x")', "#REF!(nope)"),
        # §8's leftmost rule: "Nothing about it is specific to a header cell."
        ('sum(nope1 where nope2 = "x")', "#REF!(nope1)"),
    ],
)
def test_a_header_group_aggregate_over_an_unknown_column_is_a_ref(impl, formula, want):
    """SPEC.md §8 and §4.2 rule 7: a name that does not resolve is
    `#REF!(name)`, not a refusal, and that reaches a column depending on it."""
    src = f"| id | a | t = {formula} | u = t + 1 |\n| -- | -- | -: | -: |\n| r_1 | x |  |  |\n"
    rows, _ = impl.evaluate(src)
    assert (rows[0]["t"], rows[0]["u"]) == (want, want)


@IMPLS
def test_the_predicate_of_an_unknown_aggregated_column_is_still_checked(impl):
    """§9.22 refuses a computed column in a predicate whatever the aggregated
    column is, so the `#REF!` must not hide that refusal."""
    src = (
        '| id | a | b = a * 2 | t = sum(nope where b = "x") |\n'
        "| -- | -: | -: | -: |\n| r_1 | 1 |  |  |\n"
    )
    with pytest.raises(impl.Malformed) as ex:
        impl.evaluate(src)
    assert ex.value.refusal == "computed-column-compared"
