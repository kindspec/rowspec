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
sys.path.insert(0, REF)

from rowspec import cli  # noqa: E402

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
        # No bytecode: under the size limit Python would write a truncated
        # .pyc into reference/, and every later import of it would fail.
        env=dict(os.environ, PYTHONPATH=REF, PYTHONDONTWRITEBYTECODE="1"),
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


def other_group():
    """A group this user is in other than the primary one, if any."""
    if os.name != "posix":
        return None
    return next((g for g in os.getgroups() if g != os.getegid()), None)


@pytest.mark.skipif(other_group() is None, reason="needs a second group")
def test_a_write_keeps_the_group(tmp_path):
    p = tmp_path / "t.mdtbl"
    p.write_bytes(TABLE)
    os.chown(p, -1, other_group())
    r = rowspec("add-column", "t.mdtbl", "m", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert p.stat().st_gid == other_group()


def xattrs_work(d):
    if not hasattr(os, "setxattr"):
        return False
    probe = d / "probe"
    probe.write_text("")
    try:
        os.setxattr(probe, "user.rowspec-probe", b"1")
    except OSError:
        return False
    finally:
        probe.unlink()
    return True


def test_a_write_keeps_extended_attributes(tmp_path):
    if not xattrs_work(tmp_path):
        pytest.skip("the filesystem does not take user xattrs")
    p = tmp_path / "t.mdtbl"
    p.write_bytes(TABLE)
    os.setxattr(p, "user.rowspec-test", b"kept")
    r = rowspec("add-column", "t.mdtbl", "m", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert os.getxattr(p, "user.rowspec-test") == b"kept"


def test_a_write_keeps_a_posix_acl(tmp_path):
    """An ACL is the `system.posix_acl_access` xattr on Linux, so it is kept
    with the others, and with it the access it grants another user."""
    import shutil

    if not (shutil.which("setfacl") and shutil.which("getfacl")):
        pytest.skip("needs setfacl and getfacl")
    p = tmp_path / "t.mdtbl"
    p.write_bytes(TABLE)
    if subprocess.run(["setfacl", "-m", "u:root:rw", str(p)], capture_output=True).returncode:
        pytest.skip("the filesystem does not take ACLs")

    def acl():
        out = subprocess.run(["getfacl", "-c", str(p)], capture_output=True, text=True).stdout
        return sorted(line for line in out.splitlines() if line)

    before = acl()
    assert "user:root:rw-" in before
    r = rowspec("add-column", "t.mdtbl", "m", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert acl() == before


@posix
def test_a_write_does_not_keep_the_old_mtime(tmp_path):
    """The file was edited, so its modification time is the edit's."""
    p = tmp_path / "t.mdtbl"
    p.write_bytes(TABLE)
    os.utime(p, (946684800, 946684800))  # 2000-01-01
    r = rowspec("add-column", "t.mdtbl", "m", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert p.stat().st_mtime > 946684800 + 86400


@posix
def test_the_temporary_file_is_beside_the_real_file(tmp_path, monkeypatch):
    """Renamed within one directory, the real file's: beside a symbolic link
    or in the default temporary directory, the rename could cross a
    filesystem, or land the text in the wrong place."""
    (tmp_path / "sub").mkdir()
    real = tmp_path / "sub" / "real.mdtbl"
    real.write_bytes(UNCANON)
    link = tmp_path / "link.mdtbl"
    link.symlink_to(os.path.join("sub", "real.mdtbl"))
    seen = []
    replace = os.replace

    def record(src, dst):
        seen.append((src, dst))
        replace(src, dst)

    monkeypatch.setattr(cli.os, "replace", record)
    cli._write(str(link), "| id | n |\n| --- | --- |\n| r_1 | 1 |\n")
    assert len(seen) == 1
    src, dst = seen[0]
    assert os.path.dirname(src) == os.path.dirname(os.path.realpath(link))
    assert dst == os.path.realpath(link)
    assert link.is_symlink()


@posix
def test_an_interrupt_removes_the_temporary_file(tmp_path, monkeypatch):
    p = tmp_path / "t.mdtbl"
    p.write_bytes(TABLE)

    def interrupt(fd):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli.os, "fsync", interrupt)
    with pytest.raises(KeyboardInterrupt):
        cli._write(str(p), "new text\n")
    assert p.read_bytes() == TABLE
    assert leftovers(tmp_path) == []


@posix
def test_a_refused_write_keeps_the_operating_systems_reason(tmp_path, monkeypatch, capsys):
    """A read-only file system is EROFS, not EACCES: the probe opens the
    file for writing and keeps whatever errno that gives."""
    p = tmp_path / "t.mdtbl"
    p.write_bytes(TABLE)
    real_open = os.open

    def erofs(path, flags, *a, **k):
        if flags & os.O_WRONLY:
            raise OSError(errno.EROFS, os.strerror(errno.EROFS), path)
        return real_open(path, flags, *a, **k)

    monkeypatch.setattr(cli.os, "open", erofs)
    assert cli.main(["add-column", str(p), "m"]) == 1
    assert capsys.readouterr().err == f"{p}: {os.strerror(errno.EROFS)}\n"
    assert p.read_bytes() == TABLE
