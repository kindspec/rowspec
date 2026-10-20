# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A `.mdtbl` that is not UTF-8 is refused by content, never by offset (#234).

The CLI decodes a `.mdtbl` itself, and its message was Python's codec text,
`... in position 36: ...`. It now quotes the line holding the byte and names
the byte, as a sidecar's message does (#216). The refusal is still
`bad-encoding`.
"""

import os
import re
import subprocess
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import cli  # noqa: E402

OFFSET = re.compile(r"\b(position|offset|at|line|byte) \d+\b")  # not `byte 0xE9`


def test_names_the_line_and_the_byte(tmp_path, capsys):
    p = tmp_path / "row.mdtbl"
    p.write_bytes(b"| id | n |\n| --- | --- |\n| r_1 | caf\xe9 |\n\nkey := id\n")
    assert cli.main(["check", str(p)]) == 1
    err = capsys.readouterr().err
    assert err == (
        f"{p}: not valid UTF-8: the line '| r_1 | caf\\xe9 |' holds byte 0xE9, which is"
        " not part of a valid sequence (invalid continuation byte) [bad-encoding]\n"
    )
    assert not OFFSET.search(err), err


def test_the_first_bad_line_is_the_one_named(tmp_path, capsys):
    p = tmp_path / "head.mdtbl"
    p.write_bytes(b"| id\xff | n |\n| --- | --- |\n| r_1 | caf\xe9 |\n")
    assert cli.main(["check", "--format", "github", str(p)]) == 1
    err = capsys.readouterr().err
    assert "title=rowspec [bad-encoding]::not valid UTF-8: the line '| id\\xff | n |'" in err
    assert "holds byte 0xFF, which is not part of a valid sequence (invalid start byte)" in err
    assert not OFFSET.search(err), err


def test_eval_says_the_same(tmp_path, capsys):
    """`eval` builds the refusal through the same helper as `check` (#230).
    Run as a process, so the route CI uses, `python -m rowspec`, is covered."""
    p = tmp_path / "row.mdtbl"
    p.write_bytes(b"| id | n |\n| --- | --- |\n| r_1 | caf\xe9 |\n\nkey := id\n")
    cli.main(["check", str(p)])
    want = capsys.readouterr().err
    env = dict(os.environ, PYTHONPATH=os.path.dirname(os.path.dirname(cli.__file__)))
    r = subprocess.run(
        [sys.executable, "-m", "rowspec", "eval", str(p)], capture_output=True, text=True, env=env
    )
    assert (r.returncode, r.stderr) == (1, want)
    assert "the line '| r_1 | caf\\xe9 |' holds byte 0xE9" in r.stderr, r.stderr
    assert not OFFSET.search(r.stderr), r.stderr


def test_a_lone_cr_does_not_end_the_quoted_line(tmp_path, capsys):
    """§4.1: only LF and CRLF break lines, so a lone CR between rows stays
    inside the quoted line, spelled `\\r`."""
    p = tmp_path / "cr.mdtbl"
    p.write_bytes(b"| id |\r| caf\xe9 |\n")
    assert cli.main(["check", str(p)]) == 1
    err = capsys.readouterr().err
    assert "the line '| id |\\r| caf\\xe9 |' holds byte 0xE9" in err, err
