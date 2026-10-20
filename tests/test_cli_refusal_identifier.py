# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`check` and `eval` print a refusal's SPEC §9 identifier (#101, #103).

Plain output ends the line with ` [identifier]`, the form the editing
commands already print; `--format github` puts it in the annotation's title,
a field a program reads without parsing the message. Only §9 identifiers are
printed: a warning carries none, and a CSV-mode refusal prints the §9
identifier SPEC.md §13 reads it as, never csvmode's internal rule name,
which must not become a contract by being printed.
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


def test_csv_refusals_carry_the_section_9_identifier(tmp_path, capsys):
    """A CSV refusal prints §13's §9 identifier, never csvmode's own
    `Finding.rule` name, which would become a de facto contract the moment
    it was printed; a CSV warning prints none."""
    (tmp_path / "m.csv").write_bytes(b"\xef\xbb\xbfid,name\r\nr_01,Ada\r\nr_02\r\nr_01,Repeat\r\n")
    (tmp_path / "m.csv.rowspec.json").write_text('{"key": "id"}')
    plain = cli.main(["check", str(tmp_path)]), capsys.readouterr().err
    assert plain[0] == 1
    lines = [ln for ln in plain[1].splitlines() if ln.startswith(str(tmp_path))]
    assert [TRAILING_CODE.search(ln) and TRAILING_CODE.search(ln).group() for ln in lines] == [
        "[row-field-count]",
        "[duplicate-row-id]",
        None,
        None,
    ], plain[1]
    assert all("warning: " in ln for ln in lines[2:]), lines
    assert cli.main(["check", "--format", "github", str(tmp_path)]) == 1
    titles = re.findall(r",title=([^:]*)::", capsys.readouterr().err)
    assert titles == [
        "rowspec [row-field-count]",
        "rowspec [duplicate-row-id]",
        "rowspec",
        "rowspec",
    ]
    for line in plain[1].splitlines():
        assert not re.search(r"\[(field-count|duplicate-key|bom|crlf)\]", line), line
