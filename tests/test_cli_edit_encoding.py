# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The editing commands refuse a non-UTF-8 `.mdtbl` as `check` does (#238).

Before, `_rewrite` caught only `Malformed`, so each command died with a
`UnicodeDecodeError` traceback carrying a byte offset. Run as a process, so
`python -m rowspec`, the route a user runs, is what is checked.
"""

import os
import subprocess
import sys

import pytest

REF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
BAD = b"| id | n |\n| --- | --- |\n| r_1 | caf\xe9 |\n\nkey := id\n"


def rowspec(*args):
    env = dict(os.environ, PYTHONPATH=REF)
    return subprocess.run(
        [sys.executable, "-m", "rowspec", *args], capture_output=True, text=True, env=env
    )


@pytest.mark.parametrize(
    "args",
    [
        ("add-row", "5"),
        ("add-column", "m"),
        ("delete-column", "n"),
        ("rename-column", "n", "m"),
    ],
)
def test_edit_refuses_non_utf8_like_check(tmp_path, args):
    p = tmp_path / "row.mdtbl"
    p.write_bytes(BAD)
    check = rowspec("check", str(p))
    r = rowspec(args[0], str(p), *args[1:])
    assert "Traceback" not in r.stderr, r.stderr
    assert r.returncode == 1
    assert r.stderr == check.stderr
    assert r.stderr.endswith(" [bad-encoding]\n")
    assert "position" not in r.stderr
    assert p.read_bytes() == BAD
