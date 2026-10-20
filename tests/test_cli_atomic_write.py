# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A write the CLI cannot finish leaves the file as it was, and says so (#248).

`open(path, "w").write(new)` truncated the file at once, and a write that
then failed reported its error only from a finalizer, which swallowed it: the
command printed success, exited 0 and left a truncated file. RLIMIT_FSIZE
stands in for a full disk; with SIGXFSZ ignored a write past it fails with
EFBIG as one would with ENOSPC.
"""

import errno
import hashlib
import os
import subprocess
import sys

import pytest

REF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
TABLE = b"| id | n |\n| --- | --- |\n| r_1 | 1 |\n\nkey := id\n"
UNCANON = b"| id |  n |\n| --- | --- |\n| r_1 | 1 |\n"

posix = pytest.mark.skipif(os.name != "posix", reason="RLIMIT_FSIZE is POSIX")
non_root = pytest.mark.skipif(
    os.name != "posix" or os.geteuid() == 0, reason="needs a non-root POSIX user"
)


def rowspec(*args, cwd, fsize=None):
    def cap():
        import resource
        import signal

        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, (fsize, fsize))

    return subprocess.run(
        [sys.executable, "-m", "rowspec", *args],
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONPATH=REF),
        cwd=cwd,
        preexec_fn=cap if fsize is not None else None,
    )


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def leftovers(d):
    return sorted(n for n in os.listdir(d) if n.startswith(".rowspec-"))


@posix
def test_edit_that_cannot_be_written_leaves_the_file(tmp_path):
    p = tmp_path / "t.mdtbl"
    p.write_bytes(TABLE)
    before = digest(p)
    r = rowspec("add-column", "t.mdtbl", "m", cwd=tmp_path, fsize=len(TABLE) - 9)
    assert (r.returncode, r.stdout) == (1, "")
    assert r.stderr == f"t.mdtbl: {os.strerror(errno.EFBIG)}\n", r.stderr
    assert digest(p) == before
    assert leftovers(tmp_path) == []


@posix
def test_fmt_that_cannot_be_written_leaves_the_file(tmp_path):
    p = tmp_path / "f.mdtbl"
    p.write_bytes(UNCANON)
    before = digest(p)
    r = rowspec("check", "--fmt", "f.mdtbl", cwd=tmp_path, fsize=20)
    assert r.returncode == 1
    assert r.stderr == f"f.mdtbl: {os.strerror(errno.EFBIG)}\n", r.stderr
    assert r.stdout == "1 file(s) checked, 1 refused\n"
    assert digest(p) == before
    assert leftovers(tmp_path) == []


@non_root
def test_fmt_refuses_a_read_only_file(tmp_path):
    p = tmp_path / "ro.mdtbl"
    p.write_bytes(UNCANON)
    p.chmod(0o444)
    try:
        r = rowspec("check", "--fmt", "ro.mdtbl", cwd=tmp_path)
    finally:
        p.chmod(0o644)
    assert "Traceback" not in r.stderr, r.stderr
    assert r.returncode == 1
    assert r.stderr == f"ro.mdtbl: {os.strerror(errno.EACCES)}\n"
    assert p.read_bytes() == UNCANON


@posix
def test_a_write_keeps_the_permission_bits(tmp_path):
    p = tmp_path / "t.mdtbl"
    p.write_bytes(TABLE)
    p.chmod(0o640)
    r = rowspec("add-column", "t.mdtbl", "m", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert b"| m |" in p.read_bytes()
    assert p.stat().st_mode & 0o777 == 0o640
    assert leftovers(tmp_path) == []


@posix
def test_a_write_goes_through_a_symbolic_link(tmp_path):
    real = tmp_path / "real.mdtbl"
    real.write_bytes(UNCANON)
    (tmp_path / "link.mdtbl").symlink_to("real.mdtbl")
    r = rowspec("check", "--fmt", "link.mdtbl", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "link.mdtbl").is_symlink()
    assert real.read_bytes() != UNCANON
    assert leftovers(tmp_path) == []


@non_root
def test_a_directory_that_cannot_hold_the_temporary_file(tmp_path):
    """The refusal names the table, never the temporary file it could not
    create."""
    p = tmp_path / "t.mdtbl"
    p.write_bytes(TABLE)
    tmp_path.chmod(0o555)
    try:
        r = rowspec("add-column", "t.mdtbl", "m", cwd=tmp_path)
    finally:
        tmp_path.chmod(0o755)
    assert (r.returncode, r.stdout) == (1, "")
    assert r.stderr == f"t.mdtbl: {os.strerror(errno.EACCES)}\n", r.stderr
    assert p.read_bytes() == TABLE
