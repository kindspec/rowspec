# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`rowspec eval --format github` annotates a refused `.mdtbl` (#218).

Before, the refusal was printed as a plain line whatever the format, so a CI
job failed on `eval` with nothing attached to the file. Run as a process, as
CI runs it: `cmd_eval` binds `sys.stdout` as a default argument, so pytest's
capture fixtures do not see what it prints.
"""

import os
import subprocess
import sys

REF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
DUP = "| id | n |\n| --- | --- |\n| r_1 | 1 |\n| r_1 | 2 |\n\nkey := id\n"


def rowspec(*args):
    env = dict(os.environ, PYTHONPATH=REF)
    return subprocess.run(
        [sys.executable, "-m", "rowspec", *args], capture_output=True, text=True, env=env
    )


def test_eval_github_annotates_a_refused_table(tmp_path):
    p = tmp_path / "dup.mdtbl"
    p.write_text(DUP)
    r = rowspec("eval", "--format", "github", str(p))
    assert r.returncode == 1
    assert r.stdout == (
        f"::error file={p},title=rowspec [duplicate-row-id]::duplicate key id='r_1'\n"
    )
    assert r.stderr == ""


def test_eval_plain_still_prints_the_refusal_on_stderr(tmp_path):
    p = tmp_path / "dup.mdtbl"
    p.write_text(DUP)
    r = rowspec("eval", str(p))
    assert r.returncode == 1
    assert r.stdout == ""
    assert r.stderr == f"{p}: duplicate key id='r_1' [duplicate-row-id]\n"


def test_eval_github_refusal_escapes_the_file_name(tmp_path):
    """The refusal goes through the same formatter as `check`'s, so a comma
    in the name cannot end the `file=` property early (#220)."""
    p = tmp_path / "a,b.mdtbl"
    p.write_text(DUP)
    r = rowspec("eval", "--format", "github", str(p))
    assert r.returncode == 1
    assert r.stdout == (
        f"::error file={tmp_path}/a%2Cb.mdtbl,title=rowspec [duplicate-row-id]"
        "::duplicate key id='r_1'\n"
    )
