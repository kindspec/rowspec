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
