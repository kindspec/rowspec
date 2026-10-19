# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A sidecar refusal names the sidecar by its own file name (#214):
`t.csv.rowspec.json`, or the directory's `.rowspec.json`, never a bare
`rowspec.json`, which is no file at all.

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

from rowspec.csvmode import check_file  # noqa: E402
from rowspec.table import Malformed  # noqa: E402


def refusal(tmp_path, sidecar_name, sidecar):
    p = tmp_path / "t.csv"
    p.write_bytes(b"id,n\na,1\n")
    (tmp_path / sidecar_name).write_text(json.dumps(sidecar))
    with pytest.raises(Malformed) as e:
        check_file(str(p))
    return str(e.value)


@pytest.mark.parametrize(
    "sidecar_name, sidecar",
    [
        ("t.csv.rowspec.json", {"key": "idd"}),
        (".rowspec.json", {"*.csv": {"key": "idd"}}),
    ],
    ids=["per-file", "directory"],
)
def test_a_key_naming_no_column_names_the_sidecar_file(tmp_path, sidecar_name, sidecar):
    msg = refusal(tmp_path, sidecar_name, sidecar)
    assert msg.startswith(f"{sidecar_name} declares key 'idd' but "), msg
