# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §4.1: `eol = LF / CRLF`, and every other scalar value but CR and
LF is a `char` (#144). VT, FF, U+001C-U+001E, NEL, U+2028 and U+2029 are line
breaks to Python's `str.splitlines()`, so a reader using it split one table
line in two.

Unit tests of the implementations, not conformance cases: the cases for this
rule come from an author who has not read `reference/`.
"""

import importlib
import io
import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import cli  # noqa: E402
from rowspec.csvmode import check_file  # noqa: E402
from rowspec.table import canon, parse  # noqa: E402

IMPLS = pytest.mark.parametrize("impl", ["rowspec.table", "rowspec_alt.table"])
BREAKS = pytest.mark.parametrize(
    "ch",
    ["\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"],
    ids=lambda c: f"U+{ord(c):04X}",
)
STORED = "| id | a |\n| -- | -- |\n| r_1 | x{}y |\n\nkey := id\n"


@IMPLS
@BREAKS
@pytest.mark.parametrize("eol", ["\n", "\r\n"], ids=["lf", "crlf"])
def test_a_stored_cell_holding_a_non_lf_break_is_one_line(impl, ch, eol):
    src = STORED.format(ch).replace("\n", eol)
    rows, _ = importlib.import_module(impl).evaluate(src)
    assert [(r["id"], str(r["a"])) for r in rows] == [("r_1", f"x{ch}y")]


@IMPLS
@BREAKS
def test_a_computed_cell_holding_a_non_lf_break_holds_a_value(impl, ch):
    src = f"| id | a | b = a + 1 |\n| -- | -- | -- |\n| r_1 | 1 | {ch} |\n\nkey := id\n"
    mod = importlib.import_module(impl)
    with pytest.raises(mod.Malformed) as e:
        mod.evaluate(src)
    assert e.value.refusal == "value-in-computed-cell"


@BREAKS
def test_canon_keeps_the_line_whole(ch):
    out = canon(STORED.format(ch))
    assert f"| r_1 | x{ch}y |\n" in out
    assert canon(out) == out


@BREAKS
def test_add_row_appends_after_the_whole_last_line(tmp_path, ch):
    p = tmp_path / "t.mdtbl"
    p.write_text(STORED.format(ch), encoding="utf-8", newline="")
    assert cli.cmd_add_row(str(p), ["z"], out=io.StringIO()) == 0
    _, _, rows, _, _, _ = parse(p.read_text(encoding="utf-8"))
    assert [r["a"] for r in rows] == [f"x{ch}y", "z"]


@BREAKS
def test_a_csv_field_holding_a_non_lf_break_does_not_start_a_line(tmp_path, ch):
    """SPEC.md §4.1.12: a conflict marker is a line's first seven characters,
    and a line is what LF ends."""
    p = tmp_path / "m.csv"
    p.write_bytes(f'id,n\nr_1,"x{ch}<<<<<<< y"\nr_2,2\n'.encode())
    assert check_file(str(p)) == []
