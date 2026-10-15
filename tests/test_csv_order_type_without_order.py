# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §13: a sidecar's `order_type` without `order` is refused, as
`order` without `key` is (§9.25; #184).

Unit tests of `rowspec.csvmode`, not conformance cases: the cases for this rule
come from an author who has not read `reference/`.
"""

import json
import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import cli  # noqa: E402
from rowspec.csvmode import check_file  # noqa: E402
from rowspec.table import Malformed  # noqa: E402


def write(tmp_path, sidecar):
    p = tmp_path / "t.csv"
    p.write_bytes(b"id,n\na,1\nb,2\n")
    (tmp_path / "t.csv.rowspec.json").write_text(json.dumps(sidecar))
    return str(p)


@pytest.mark.parametrize(
    "sidecar",
    [{"key": "id", "order_type": "number"}, {"order_type": "number"}, {"order_type": "text"}],
    ids=["with-key", "alone", "a-type-the-column-is-not"],
)
def test_order_type_without_order_is_refused(tmp_path, sidecar):
    with pytest.raises(Malformed, match="'order_type' requires 'order'"):
        check_file(write(tmp_path, sidecar))


def test_order_type_without_order_is_a_refusal_on_the_cli(tmp_path, capsys):
    write(tmp_path, {"key": "id", "order_type": "number"})
    assert cli.main(["check", str(tmp_path)]) == 1


def test_order_type_with_order_is_accepted(tmp_path):
    assert check_file(write(tmp_path, {"key": "id", "order": "n", "order_type": "number"})) == []


def test_the_directory_sidecar_refuses_it_too(tmp_path):
    (tmp_path / ".rowspec.json").write_text(json.dumps({"*.csv": {"order_type": "date"}}))
    p = tmp_path / "a.csv"
    p.write_bytes(b"id,n\na,1\n")
    with pytest.raises(Malformed, match="'order_type' requires 'order'"):
        check_file(str(p))
