# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A quoted value or line never shows an escape in part, and a literal
backslash in a quoted line never reads as a byte (#239)."""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import cli  # noqa: E402
from rowspec.sidecar import _quote_at  # noqa: E402
from rowspec.table import _show  # noqa: E402

ZW = "\u200b"


def test_show_truncates_between_escapes():
    assert _show("a" * 35 + ZW + "b" * 10) == "'" + "a" * 35 + "\u2026'"
    assert _show("a" * 33 + ZW + "b" * 10) == "'" + "a" * 33 + "\\u200b\u2026'"


def test_show_is_unchanged_where_no_escape_is_cut():
    assert _show("x" * 50) == "'" + "x" * 39 + "\u2026'"
    assert _show("abc") == "'abc'"
    assert _show("a\x1bb") == "'a\\x1bb'"


def test_window_starts_between_escapes():
    line = '{"key": "' + ZW * 4 + "zw" + ZW + "\udce9" + '"}'
    q = _quote_at(line, line.index("\udce9"))
    assert q == "'\u2026zw\\u200b\\xe9\"}'", q


def test_literal_backslash_is_doubled():
    line = '{"a": "\\xe9\udce9"}'
    assert _quote_at(line, line.index("\udce9")) == '\'{"a": "\\\\xe9\\xe9"}\''


def test_sidecar_refusal_tells_text_from_byte(tmp_path, capsys):
    (tmp_path / "e.csv").write_bytes(b"id,v\n1,a\n")
    (tmp_path / "e.csv.rowspec.json").write_bytes(b'{"a": "\\xe9\xe9"}\n')
    assert cli.main(["check", str(tmp_path / "e.csv")]) == 1
    err = capsys.readouterr().err
    assert 'the line \'{"a": "\\\\xe9\\xe9"}\' holds byte 0xE9' in err, err


def test_invalid_json_line_tells_an_escape_from_a_character(tmp_path, capsys):
    """In JSON, `\\u200b` is six characters of text and U+200B is one
    invisible character. The quote spells the second `\\u200b`, so the
    first has to be `\\\\u200b`."""
    (tmp_path / "j.csv").write_bytes(b"id,v\n1,a\n")
    (tmp_path / "j.csv.rowspec.json").write_bytes(b'{"\\u200b\xe2\x80\x8b" x}\n')
    assert cli.main(["check", str(tmp_path / "j.csv")]) == 1
    err = capsys.readouterr().err
    assert "in the line '{\"\\\\u200b\\u200b\" x}'" in err, err
