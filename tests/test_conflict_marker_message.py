# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A `.mdtbl` conflict marker is reported by entity, never by line (#196).

Errors name entities, never offsets: the message quotes the marker, as CSV
mode does, and names the nearest row by its key, else the header row. The
refusal identifier is §9.1's and is unchanged. These are unit tests of the
reference implementation's wording, not conformance cases.
"""

import pytest
from rowspec import cli
from rowspec.table import Malformed, parse

ROWS = "| id | a |\n| -- | -- |\n| r_1 | 1 |\n| r_2 | 2 |\n| r_3 | 3 |\n"


def _refuse(text):
    with pytest.raises(Malformed) as e:
        parse(text)
    assert e.value.refusal == "conflict-marker"
    return str(e.value)


def test_the_issue_reproduction_quotes_the_marker_and_no_line_number():
    msg = _refuse("<<<<<<< ours\n| id | a |\n| -- | -- |\n| r_1 | 1 |\n\nkey := id\n")
    assert msg == "unresolved conflict marker '<<<<<<< ours' near the header row"


def test_a_marker_between_rows_names_the_row_by_its_key():
    text = (
        "| id | a |\n| -- | -- |\n| r_1 | 1 |\n<<<<<<< HEAD\n| r_2 | 2 |\n"
        "=======\n| r_2 | 9 |\n>>>>>>> theirs\n| r_3 | 3 |\n\nkey := id\n"
    )
    assert _refuse(text) == "unresolved conflict marker '<<<<<<< HEAD' near row id='r_2'"


def test_the_key_column_is_used_not_the_first_column():
    text = "| a | id |\n| -- | -- |\n| 1 | r_1 |\n||||||| base\n| 2 | r_2 |\n\nkey := id\n"
    assert _refuse(text) == "unresolved conflict marker '||||||| base' near row id='r_2'"


def test_a_closing_marker_tie_goes_to_the_row_above():
    text = "| id | a |\n| -- | -- |\n| r_1 | 1 |\n>>>>>>> theirs\n| r_2 | 2 |\n\nkey := id\n"
    assert _refuse(text) == "unresolved conflict marker '>>>>>>> theirs' near row id='r_1'"


def test_without_a_key_the_row_is_named_by_its_first_column():
    text = "| id | a |\n| -- | -- |\n| r_1 | 1 |\n=======\n"
    assert _refuse(text) == "unresolved conflict marker '=======' near row id='r_1'"


def test_with_no_table_line_the_marker_alone():
    assert _refuse("<<<<<<< ours\nkey := id\n") == "unresolved conflict marker '<<<<<<< ours'"


def test_a_long_marker_is_truncated_as_csv_mode_truncates_it():
    msg = _refuse("<<<<<<< " + "x" * 100 + "\n")
    assert msg == "unresolved conflict marker '<<<<<<< " + "x" * 51 + "…'"


def test_the_cli_reports_it_without_an_offset(tmp_path, capsys):
    p = tmp_path / "t.mdtbl"
    p.write_text(ROWS.replace("| r_2 | 2 |\n", "<<<<<<< ours\n| r_2 | 2 |\n") + "\nkey := id\n")
    assert cli.main(["check", str(p)]) == 1
    err = capsys.readouterr()
    out = err.out + err.err
    assert f"{p}: unresolved conflict marker '<<<<<<< ours' near row id='r_2'" in out
    assert "line " not in out
