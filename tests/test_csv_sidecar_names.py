# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §13: a sidecar names a column as §9.2 compares names in CSV mode,
after trimming ASCII space and tab only and after NFC. `""` names an
empty-headed column, a name that names no column is refused, and two
`columns` members naming one column are refused (#181, #182, #183).

Unit tests of `rowspec.csvmode`, not conformance cases: the cases for this rule
come from an author who has not read `reference/`.
"""

import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec.csvmode import check_file  # noqa: E402
from rowspec.table import Malformed  # noqa: E402


def check(tmp_path, data, sidecar_json):
    """The sidecar is raw JSON text, so `\\u` escapes reach the parser."""
    p = tmp_path / "t.csv"
    p.write_bytes(data.encode("utf-8"))
    (tmp_path / "t.csv.rowspec.json").write_text(sidecar_json, encoding="utf-8")
    return sorted({f.rule for f in check_file(str(p))})


# --- #181: an empty name ------------------------------------------------------


@pytest.mark.parametrize(
    "sidecar",
    ['{"key": ""}', '{"key": "id", "order": ""}', '{"columns": {"": "number"}}'],
    ids=["key", "order", "columns"],
)
def test_an_empty_name_with_no_empty_headed_column_names_no_column(tmp_path, sidecar):
    with pytest.raises(Malformed, match="no such column"):
        check(tmp_path, "id,n\na,1\nb,2\n", sidecar)


def test_an_empty_key_names_the_empty_headed_column(tmp_path):
    assert check(tmp_path, "id,\na,x\nb,x\n", '{"key": ""}') == ["duplicate-key"]
    assert check(tmp_path, "id,\na,x\nb,y\n", '{"key": ""}') == []


def test_an_empty_order_names_the_empty_headed_column(tmp_path):
    side = '{"key": "id", "order": ""}'
    assert check(tmp_path, "id,\na,1\nb,x\n", side) == ["order-mixed-types"]
    assert check(tmp_path, "id,\na,1\nb,2\n", side) == []


# --- #182: names are trimmed of ASCII space and tab -------------------------


@pytest.mark.parametrize("name", [" id", "id ", "\tid", "id\t", " \tid\t "])
def test_a_key_name_is_trimmed_of_ascii_space_and_tab(tmp_path, name):
    side = '{"key": "' + name.replace("\t", "\\t") + '"}'
    assert check(tmp_path, "id,n\na,1\na,2\n", side) == ["duplicate-key"]


def test_an_order_name_is_trimmed(tmp_path):
    side = '{"key": "id", "order": " n\\t"}'
    assert check(tmp_path, "id,n\na,1\nb,x\n", side) == ["order-mixed-types"]


def test_a_columns_name_is_trimmed(tmp_path):
    assert check(tmp_path, "id,n\na,x\n", '{"columns": {" n ": "number"}}') == ["column-type"]


@pytest.mark.parametrize("name", [" ", "\\t", " \\t "])
def test_a_name_of_ascii_space_and_tab_names_the_empty_headed_column(tmp_path, name):
    assert check(tmp_path, "id,\na,x\nb,x\n", '{"key": "' + name + '"}') == ["duplicate-key"]


@pytest.mark.parametrize("name", ["id\\u00a0", "\\u00a0id", "id\\u3000"])
def test_a_non_ascii_space_at_the_edge_of_a_name_is_part_of_it(tmp_path, name):
    with pytest.raises(Malformed, match="no such column"):
        check(tmp_path, "id,n\na,1\n", '{"key": "' + name + '"}')


def test_a_name_is_compared_after_nfc(tmp_path):
    side = '{"key": "id", "order": "cafe\\u0301"}'
    assert check(tmp_path, "id,caf\u00e9\na,1\nb,x\n", side) == ["order-mixed-types"]


# --- #183: two columns members naming one column -----------------------------


@pytest.mark.parametrize(
    "members",
    [
        '"caf\\u00e9": "number", "cafe\\u0301": "number"',
        '"caf\\u00e9": "number", "cafe\\u0301": "text"',
        '"n": "number", " n": "number"',
        '"n": "number", "n\\t": "text"',
        '"": "text", " ": "text"',
    ],
    ids=["nfc-and-nfd", "nfc-and-nfd-differing", "padded", "tab-padded", "empty-and-space"],
)
def test_two_columns_members_naming_one_column_are_refused(tmp_path, members):
    with pytest.raises(Malformed, match="names column .* twice"):
        check(tmp_path, "id,caf\u00e9,n,\na,1,1,x\n", '{"columns": {' + members + "}}")


def test_columns_members_naming_different_columns_are_accepted(tmp_path):
    side = '{"columns": {"n": "number", "n\\u00a0": "text"}}'
    assert check(tmp_path, "id,n,n\u00a0\na,1,x\n", side) == []
