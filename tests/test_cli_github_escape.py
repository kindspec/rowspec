# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`--format github` escapes what GitHub's workflow commands require (#220).

A message escapes `%`, CR and LF; a property value such as `file=` escapes
those and `:` and `,`. Unescaped, GitHub reads a different file name or
message from the one written: `a,b.csv` ends the `file=` property at `a`, and
`%25` in a key is shown as `%`.
"""

import json
import os
import subprocess
import sys

REF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
sys.path.insert(0, REF)

from rowspec import cli  # noqa: E402

CONFLICTED = b"<<<<<<< HEAD\na,b\n1,2\n"


def test_message_escapes_percent_cr_lf():
    assert cli._gh_data("50%25\r\nx") == "50%2525%0D%0Ax"


def test_property_also_escapes_colon_and_comma():
    assert cli._gh_prop("c:d,e%\r\n") == "c%3Ad%2Ce%25%0D%0A"


def test_check_escapes_the_file_name(tmp_path, capsys):
    (tmp_path / "a,b%25.csv").write_bytes(CONFLICTED)
    (tmp_path / "c:d.csv").write_bytes(CONFLICTED)
    cli.main(["check", "--format", "github", str(tmp_path)])
    err = capsys.readouterr().err
    root = cli._gh_prop(str(tmp_path))
    assert f"::error file={root}/a%2Cb%2525.csv,title=rowspec::" in err, err
    assert f"::error file={root}/c%3Ad.csv,title=rowspec::" in err, err


def test_check_escapes_percent_in_the_message(tmp_path, capsys):
    (tmp_path / "pct.csv").write_bytes(b"id,n\n50%25,1\n50%25,2\n")
    (tmp_path / "pct.csv.rowspec.json").write_text(json.dumps({"key": "id"}))
    cli.main(["check", "--format", "github", str(tmp_path)])
    err = capsys.readouterr().err
    assert "duplicate key id='50%2525'" in err, err


def test_eval_escapes_the_file_name(tmp_path):
    """Run as a process: `cmd_eval` binds `sys.stdout` as a default argument,
    so pytest's capture fixtures do not see what it prints."""
    p = tmp_path / "x,y%25.mdtbl"
    p.write_text("| id | a | t = zz |\n| --- | --- | --- |\n| r_1 | 1 |  |\n\nkey := id\n")
    env = dict(os.environ, PYTHONPATH=REF)
    r = subprocess.run(
        [sys.executable, "-m", "rowspec", "eval", "--format", "github", str(p)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 1
    want = f"::error file={cli._gh_prop(str(tmp_path))}/x%2Cy%2525.mdtbl,title=rowspec::"
    assert want in r.stdout, r.stdout
