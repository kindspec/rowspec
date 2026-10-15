# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §13: a CSV column name is trimmed of ASCII space and tab only, so a
header cell holding only U+00A0 or another Unicode space is a non-empty name,
and a header of such cells is a header row (#154).

Unit tests of the reference implementation, not conformance cases: the cases
for this rule come from an author who has not read `reference/`.
"""

import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec.csvmode import check_file  # noqa: E402
from rowspec.table import Malformed  # noqa: E402

SPACES = pytest.mark.parametrize(
    "sp", ["\u00a0", "\u2003", "\u202f"], ids=["nbsp", "em", "narrow-nbsp"]
)


def check(tmp_path, body):
    p = tmp_path / "t.csv"
    p.write_text(body, encoding="utf-8")
    return check_file(str(p))


def rules(findings):
    return sorted({f.rule for f in findings})


@SPACES
def test_a_header_of_one_unicode_space_is_a_header(tmp_path, sp):
    assert check(tmp_path, f"{sp}\nr1\n") == []


def test_a_header_of_two_different_unicode_spaces_is_two_names(tmp_path):
    """The issue's file: `<U+00A0>,<U+2003>` names two distinct columns."""
    assert check(tmp_path, "\u00a0,\u2003\nr1,1\n") == []


@SPACES
def test_a_header_of_one_unicode_space_twice_is_a_duplicate_column(tmp_path, sp):
    """Read as names, the two cells are one name, so §9.2 decides: the file is
    refused as a duplicate column, not as a file with no header row."""
    assert rules(check(tmp_path, f"{sp},{sp}\nr1,1\n")) == ["duplicate-column"]


@pytest.mark.parametrize("cell", [" ", "\t", " \t "], ids=["space", "tab", "mixed"])
def test_a_header_of_ascii_space_and_tab_is_still_refused(tmp_path, cell):
    """The same header with ASCII space and tab, which §13 does trim, is two
    empty names and still refused, so the tests above are about the
    character and not about any header being accepted."""
    try:
        found = check(tmp_path, f"{cell},{cell}\nr1,1\n")
    except Malformed:
        return
    assert any(f.level == "refuse" for f in found)


@pytest.mark.parametrize("ch", ["\x0b", "\x0c"], ids=["vt", "ff"])
def test_a_file_of_one_vt_or_ff_name_is_a_header_only_file(tmp_path, ch):
    """VT and FF are not trimmed by §13, so a file holding only one of them
    is a header of one name, as `<VT>,x` is, and not an empty file."""
    assert check(tmp_path, f"{ch}\n") == []


@pytest.mark.parametrize(
    "body", ["", "\n", " \t\n", "\r\n\r\n"], ids=["empty", "lf", "wsp", "crlf"]
)
def test_a_file_of_ascii_space_tab_and_line_breaks_is_still_empty(tmp_path, body):
    """Control: what the empty-file check still trims."""
    with pytest.raises(Malformed, match="no table"):
        check(tmp_path, body)
