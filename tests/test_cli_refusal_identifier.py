# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`check` and `eval` print a `.mdtbl` refusal's SPEC §9 identifier (#101).

Plain output ends the line with ` [identifier]`, the form the editing
commands already print; `--format github` puts it in the annotation's title,
a field a program reads without parsing the message. Only §9 identifiers are
printed: a warning carries none, and neither does CSV mode, whose findings
have no §9 identifiers yet and whose internal rule names must not become a
contract by being printed.
"""

import os
import re
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import cli  # noqa: E402

DUP = "| id | n |\n| --- | --- |\n| r_1 | 1 |\n| r_1 | 2 |\n\nkey := id\n"
TRAILING_CODE = re.compile(r"\[[a-z0-9-]+\]$")


def test_check_plain_ends_the_line_with_the_identifier(tmp_path, capsys):
    p = tmp_path / "dup.mdtbl"
    p.write_text(DUP)
    assert cli.main(["check", str(p)]) == 1
    assert capsys.readouterr().err == f"{p}: duplicate key id='r_1' [duplicate-row-id]\n"


def test_check_github_puts_the_identifier_in_the_title(tmp_path, capsys):
    p = tmp_path / "dup.mdtbl"
    p.write_text(DUP)
    assert cli.main(["check", "--format", "github", str(p)]) == 1
    assert capsys.readouterr().err == (
        f"::error file={p},title=rowspec [duplicate-row-id]::duplicate key id='r_1'\n"
    )


def test_eval_plain_ends_the_line_with_the_identifier(tmp_path, capsys):
    p = tmp_path / "dup.mdtbl"
    p.write_text(DUP)
    assert cli.main(["eval", str(p)]) == 1
    assert capsys.readouterr().err == f"{p}: duplicate key id='r_1' [duplicate-row-id]\n"


def test_non_utf8_mdtbl_is_bad_encoding(tmp_path, capsys):
    p = tmp_path / "enc.mdtbl"
    p.write_bytes(b"| id\xff | n |\n| --- | --- |\n| r_1 | 1 |\n")
    assert cli.main(["check", str(p)]) == 1
    assert capsys.readouterr().err.rstrip("\n").endswith(" [bad-encoding]")
    assert cli.main(["check", "--format", "github", str(p)]) == 1
    assert "title=rowspec [bad-encoding]::not valid UTF-8" in capsys.readouterr().err


def test_a_warning_carries_no_identifier(tmp_path, capsys):
    (tmp_path / "crlf.csv").write_bytes(b"a,b\r\n1,2\r\n")
    (tmp_path / "fmt.mdtbl").write_text("| id |  n |\n| --- | --- |\n| r_1 | 1 |\n")
    for fmt in ("plain", "github"):
        cli.main(["check", "--fmt-check", "--format", fmt, str(tmp_path)])
        err = capsys.readouterr().err
        assert "CRLF" in err and "not in canonical form" in err, err
        for line in err.splitlines():
            assert not TRAILING_CODE.search(line), line
            assert "title=rowspec::" in line or not line.startswith("::"), line


def test_csv_findings_carry_no_identifier(tmp_path, capsys):
    """Neither a §9 identifier nor csvmode's own `Finding.rule` names, which
    would become a de facto contract the moment they were printed."""
    (tmp_path / "m.csv").write_bytes(
        b"\xef\xbb\xbfid,name\r\nr_01,Ada\r\nr_02\r\nr_01,Repeat\r\n<<<<<<< HEAD\r\n"
    )
    (tmp_path / "m.csv.rowspec.json").write_text('{"key": "id"}')
    for fmt in ("plain", "github"):
        assert cli.main(["check", "--format", fmt, str(tmp_path)]) == 1
        err = capsys.readouterr().err
        assert err.count("\n") >= 3, err
        for line in err.splitlines():
            assert not TRAILING_CODE.search(line), line
            assert not re.search(r"\[(field-count|duplicate-key|conflict-marker|bom)\]", line)
            if line.startswith("::"):
                assert ",title=rowspec::" in line, line
