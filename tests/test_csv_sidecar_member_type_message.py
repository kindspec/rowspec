# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A sidecar member that is not a string is told what it must be (#215).

SPEC.md §13: `order_type` is "one of the strings `number`, `date` or
`text`", and `delimiter` is a string of one Unicode scalar value. Neither is
a column name, which is what the refusal used to say for both.

Unit tests of `rowspec.sidecar`, not conformance cases: the cases for this rule
come from an author who has not read `reference/`.
"""

import json
import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec.csvmode import check_file  # noqa: E402
from rowspec.table import Malformed  # noqa: E402


def refusal(tmp_path, sidecar):
    p = tmp_path / "t.csv"
    p.write_bytes(b"id,n\na,1\n")
    (tmp_path / "t.csv.rowspec.json").write_text(json.dumps(sidecar))
    with pytest.raises(Malformed) as e:
        check_file(str(p))
    return str(e.value)


@pytest.mark.parametrize("value", [3, None, ["number"]], ids=["int", "null", "array"])
def test_a_non_string_order_type_names_the_three_types(tmp_path, value):
    msg = refusal(tmp_path, {"key": "id", "order": "n", "order_type": value})
    assert "'order_type' must be one of the strings 'number', 'date' or 'text', not " in msg
    assert "column name" not in msg


def test_a_non_string_delimiter_says_it_is_one_scalar_value(tmp_path):
    msg = refusal(tmp_path, {"delimiter": 9})
    assert "'delimiter' must be a string of one Unicode scalar value, not int" in msg
    assert "column name" not in msg


@pytest.mark.parametrize("member", ["key", "order"])
def test_a_non_string_key_or_order_still_says_column_name(tmp_path, member):
    sidecar = {"key": "id", "order": "n", member: 7}
    msg = refusal(tmp_path, sidecar)
    assert f"{member!r} must be a column name, not int" in msg
