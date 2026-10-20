# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`rowspec eval` refuses a non-UTF-8 `.mdtbl` the way `check` does (#230).

Before, the decode error escaped as a traceback, and a non-UTF-8 file that
`eval` would have skipped aborted the whole run. Run as a process, as CI runs
it, so a traceback is seen as one.
"""

import os
import subprocess
import sys

REF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
OK = "| id | n |\n| --- | --- |\n| r_1 | 1 |\n"


def rowspec(*args):
    env = dict(os.environ, PYTHONPATH=REF)
    return subprocess.run(
        [sys.executable, "-m", "rowspec", *args], capture_output=True, text=True, env=env
    )


def test_eval_refuses_non_utf8_like_check(tmp_path):
    p = tmp_path / "enc.mdtbl"
    p.write_bytes(b"| id\xff | n |\n| --- | --- |\n| r_1 | 1 |\n")
    check = rowspec("check", str(p))
    r = rowspec("eval", str(p))
    assert "Traceback" not in r.stderr, r.stderr
    assert (r.returncode, r.stderr) == (check.returncode, check.stderr)
    assert r.stderr.startswith(f"{p}: not valid UTF-8: ")
    assert r.stderr.endswith(" [bad-encoding]\n")


def test_eval_github_annotates_non_utf8_like_check(tmp_path):
    p = tmp_path / "enc.mdtbl"
    p.write_bytes(b"| id\xff | n |\n| --- | --- |\n| r_1 | 1 |\n")
    check = rowspec("check", "--format", "github", str(p))
    r = rowspec("eval", "--format", "github", str(p))
    assert r.returncode == 1
    assert (r.stdout, r.stderr) == (check.stderr, "")
    assert r.stdout.startswith(f"::error file={p},title=rowspec [bad-encoding]::not valid UTF-8")


def test_eval_skips_a_non_utf8_file_it_does_not_evaluate(tmp_path):
    """`a.csv` sorts before `ok.mdtbl`, so a run that stopped at the CSV
    instead of skipping it would never print the table."""
    (tmp_path / "a.csv").write_bytes(b"a,b\n\xff,2\n")
    (tmp_path / "ok.mdtbl").write_text(OK)
    r = rowspec("eval", str(tmp_path))
    assert "Traceback" not in r.stderr, r.stderr
    assert r.returncode == 0
    assert f"{tmp_path / 'ok.mdtbl'}\n" in r.stdout, r.stdout
