# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The editing commands refuse a missing file or a directory cleanly (#243).

Before, `_rewrite` did not catch `OSError`, so each command died with a
`FileNotFoundError` or `IsADirectoryError` traceback. Run as a process, so
`python -m rowspec`, the route a user runs, is what is checked.
"""

import errno
import os
import subprocess
import sys

import pytest

REF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
COMMANDS = [
    ("add-row", "5"),
    ("add-column", "m"),
    ("delete-column", "n"),
    ("rename-column", "n", "m"),
]


def rowspec(*args, cwd):
    env = dict(os.environ, PYTHONPATH=REF)
    return subprocess.run(
        [sys.executable, "-m", "rowspec", *args], capture_output=True, text=True, env=env, cwd=cwd
    )


@pytest.mark.parametrize("args", COMMANDS)
def test_missing_file_is_named(tmp_path, args):
    r = rowspec(args[0], "nope.mdtbl", *args[1:], cwd=tmp_path)
    assert "Traceback" not in r.stderr, r.stderr
    assert (r.returncode, r.stdout) == (1, "")
    assert r.stderr == f"nope.mdtbl: {os.strerror(errno.ENOENT)}\n"
    assert not (tmp_path / "nope.mdtbl").exists()


@pytest.mark.parametrize("args", COMMANDS)
def test_directory_is_named(tmp_path, args):
    (tmp_path / "dir.mdtbl").mkdir()
    r = rowspec(args[0], "dir.mdtbl", *args[1:], cwd=tmp_path)
    assert "Traceback" not in r.stderr, r.stderr
    assert (r.returncode, r.stdout) == (1, "")
    assert r.stderr == f"dir.mdtbl: {os.strerror(errno.EISDIR)}\n"
    assert (tmp_path / "dir.mdtbl").is_dir()


TABLE = b"| id | n |\n| --- | --- |\n| r_1 | 1 |\n\nkey := id\n"


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="needs a non-root POSIX user")
@pytest.mark.parametrize("args", COMMANDS)
def test_read_only_file_is_named(tmp_path, args):
    """The write is under the same refusal as the read: a read-only file
    raised PermissionError from `open(path, "w")`."""
    p = tmp_path / "ro.mdtbl"
    p.write_bytes(TABLE)
    p.chmod(0o444)
    try:
        r = rowspec(args[0], "ro.mdtbl", *args[1:], cwd=tmp_path)
    finally:
        p.chmod(0o644)
    assert "Traceback" not in r.stderr, r.stderr
    assert (r.returncode, r.stdout) == (1, "")
    assert r.stderr == f"ro.mdtbl: {os.strerror(errno.EACCES)}\n"
    assert p.read_bytes() == TABLE


@pytest.mark.parametrize("args", COMMANDS)
def test_empty_file_name_is_a_usage_error(tmp_path, args):
    r = rowspec(args[0], "", *args[1:], cwd=tmp_path)
    assert "Traceback" not in r.stderr, r.stderr
    assert r.returncode == 2
    assert r.stderr.endswith(f"rowspec {args[0]}: error: the file name is empty\n"), r.stderr
