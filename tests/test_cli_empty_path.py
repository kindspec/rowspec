# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`check` and `eval` refuse an empty path as a usage error, exit 2 (#250).

Before, it was reported as a missing file named by nothing,
`: No such file or directory`, and the other paths were still checked.
Run as a process, so `python -m rowspec` is what is checked.
"""

import os
import subprocess
import sys

import pytest

REF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")


def rowspec(*args, cwd):
    env = dict(os.environ, PYTHONPATH=REF)
    return subprocess.run(
        [sys.executable, "-m", "rowspec", *args], capture_output=True, text=True, env=env, cwd=cwd
    )


@pytest.mark.parametrize(
    "args",
    [
        ("check", ""),
        ("eval", ""),
        ("check", "--format", "github", ""),
        ("eval", "--format", "github", ""),
        ("check", "ok.mdtbl", ""),
    ],
)
def test_empty_path_is_a_usage_error(tmp_path, args):
    (tmp_path / "ok.mdtbl").write_text("| id |\n| --- |\n| r_1 |\n")
    r = rowspec(*args, cwd=tmp_path)
    assert "Traceback" not in r.stderr, r.stderr
    assert (r.returncode, r.stdout) == (2, "")
    assert r.stderr.endswith(f"rowspec {args[0]}: error: a path is empty\n"), r.stderr


def test_a_non_empty_path_is_unaffected(tmp_path):
    (tmp_path / "ok.mdtbl").write_text("| id |\n| --- |\n| r_1 |\n")
    r = rowspec("check", "ok.mdtbl", cwd=tmp_path)
    assert (r.returncode, r.stdout) == (0, "1 file(s) checked, 0 refused\n")
