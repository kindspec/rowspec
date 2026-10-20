# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`check` and `eval` refuse a path they cannot read, naming it (#246).

Before, a missing path given on the command line escaped as a
`FileNotFoundError` traceback. Run as a process, so `python -m rowspec`, the
route CI runs, is what is checked.
"""

import errno
import os
import subprocess
import sys

import pytest

REF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
ENOENT = os.strerror(errno.ENOENT)


def rowspec(*args, cwd):
    env = dict(os.environ, PYTHONPATH=REF)
    return subprocess.run(
        [sys.executable, "-m", "rowspec", *args], capture_output=True, text=True, env=env, cwd=cwd
    )


@pytest.mark.parametrize("name", ["nope.mdtbl", "nope.csv"])
def test_check_names_a_missing_file(tmp_path, name):
    r = rowspec("check", name, cwd=tmp_path)
    assert "Traceback" not in r.stderr, r.stderr
    assert r.returncode == 1
    assert r.stderr == f"{name}: {ENOENT}\n"
    assert r.stdout == "1 file(s) checked, 1 refused\n"


def test_check_github_annotates_a_missing_file(tmp_path):
    r = rowspec("check", "--format", "github", "nope.mdtbl", cwd=tmp_path)
    assert r.returncode == 1
    assert r.stderr == f"::error file=nope.mdtbl,title=rowspec::{ENOENT}\n"


@pytest.mark.parametrize("name", ["nope.mdtbl", "nope.csv"])
def test_eval_names_a_missing_file(tmp_path, name):
    r = rowspec("eval", name, cwd=tmp_path)
    assert "Traceback" not in r.stderr, r.stderr
    assert (r.returncode, r.stdout) == (1, "")
    assert r.stderr == f"{name}: {ENOENT}\n"


def test_eval_github_annotates_a_missing_file(tmp_path):
    r = rowspec("eval", "--format", "github", "nope.mdtbl", cwd=tmp_path)
    assert (r.returncode, r.stderr) == (1, "")
    assert r.stdout == f"::error file=nope.mdtbl,title=rowspec::{ENOENT}\n"


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="needs a non-root POSIX user")
def test_an_unreadable_sidecar_is_named(tmp_path):
    (tmp_path / "d.csv").write_text("id,v\n1,a\n")
    side = tmp_path / "d.csv.rowspec.json"
    side.write_text('{"key": "id"}')
    side.chmod(0)
    try:
        r = rowspec("check", "d.csv", cwd=tmp_path)
    finally:
        side.chmod(0o644)
    assert r.returncode == 1
    assert r.stderr == f"d.csv: {os.strerror(errno.EACCES)}: d.csv.rowspec.json\n", r.stderr
