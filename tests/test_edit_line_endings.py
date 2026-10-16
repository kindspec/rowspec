# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The editing helpers keep a file's line endings and refuse a line break in a
value (#194).

SPEC.md §3: LF and CRLF both round-trip byte-exactly, and §4.1.1: an
unterminated last line stays unterminated. So `set_cell` writes the edited row
with that row's own ending, and `add-row` gives a new row the file's. §4.1's
`char` excludes CR and LF, so a value holding either cannot be a cell: both
helpers refuse it rather than write a table that no longer parses.

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
from rowspec.table import parse  # noqa: E402

IMPLS = pytest.mark.parametrize("impl", ["rowspec.table", "rowspec_alt.table"])
CRLF = "| id | a |\r\n| --- | --- |\r\n| r_1 | x |\r\n| r_2 | y |\r\n\r\nkey := id\r\n"
BREAKS = pytest.mark.parametrize("value", ["p\nq", "p\rq", "p\r\nq", "p\n", "\r"])


def edited(impl, text, row, value):
    m = importlib.import_module(impl)
    return m.render(m.set_cell(m.structure(text), row, "a", value))


@IMPLS
@pytest.mark.parametrize("eol", ["\n", "\r\n"])
def test_set_cell_keeps_the_rows_line_ending(impl, eol):
    text = CRLF.replace("\r\n", eol)
    assert edited(impl, text, "r_1", "z") == text.replace("| r_1 | x |", "| r_1 | z |")


@IMPLS
def test_set_cell_keeps_each_rows_own_ending_in_a_mixed_file(impl):
    text = "| id | a |\n| --- | --- |\n| r_1 | x |\r\n| r_2 | y |\n\nkey := id\n"
    assert edited(impl, text, "r_1", "z") == text.replace("| r_1 | x |", "| r_1 | z |")
    assert edited(impl, text, "r_2", "z") == text.replace("| r_2 | y |", "| r_2 | z |")


@IMPLS
def test_set_cell_leaves_an_unterminated_last_row_unterminated(impl):
    text = "key := id\r\n\r\n| id | a |\r\n| --- | --- |\r\n| r_1 | x |"
    assert edited(impl, text, "r_1", "z") == text.replace("| r_1 | x |", "| r_1 | z |")


@IMPLS
@BREAKS
def test_set_cell_refuses_a_line_break(impl, value):
    m = importlib.import_module(impl)
    st = m.structure(CRLF)
    with pytest.raises(m.Malformed, match="line break"):
        m.set_cell(st, "r_1", "a", value)
    assert m.render(st) == CRLF


@pytest.mark.parametrize(
    "text",
    [CRLF, CRLF.replace("\r\n", "\n")],
    ids=["crlf", "lf"],
)
def test_add_row_gives_the_new_row_the_files_ending(tmp_path, text):
    p = tmp_path / "t.mdtbl"
    p.write_bytes(text.encode())
    assert cli.cmd_add_row(str(p), ["z"], out=io.StringIO(), end=True) == 0
    out = p.read_bytes().decode()
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = out.split(eol)
    assert lines[4].startswith("| r_") and lines[4].endswith(" | z |")
    assert out.replace(lines[4] + eol, "", 1) == text


@pytest.mark.parametrize("eol", ["\n", "\r\n"])
def test_add_row_after_an_unterminated_last_row(tmp_path, eol):
    text = f"key := id{eol}{eol}| id | a |{eol}| --- | --- |{eol}| r_1 | x |"
    p = tmp_path / "t.mdtbl"
    p.write_bytes(text.encode())
    assert cli.cmd_add_row(str(p), ["z"], out=io.StringIO(), end=True) == 0
    out = p.read_bytes().decode()
    assert out.startswith(text + eol + "| r_") and out.endswith(" | z |")
    assert [r["a"] for r in parse(out)[2]] == ["x", "z"]


@BREAKS
def test_add_row_refuses_a_line_break(tmp_path, capsys, value):
    p = tmp_path / "t.mdtbl"
    p.write_bytes(CRLF.encode())
    assert cli.cmd_add_row(str(p), [value], out=io.StringIO()) == 1
    assert "line break" in capsys.readouterr().err
    assert p.read_bytes() == CRLF.encode()
