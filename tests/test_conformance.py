# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The conformance suite and the mutation gate, as tests.

The suite is the deliverable; running it under pytest is a convenience, not the
definition. `just conform` runs the same cases directly.
"""

import fcntl
import os
import selectors
import shutil
import subprocess
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF = os.path.join(ROOT, "conformance")


def _run(script, *args):
    return subprocess.run([sys.executable, script, *args], cwd=CONF, capture_output=True, text=True)


def test_conformance_suite_passes():
    r = _run("run_cases.py")
    assert r.returncode == 0, r.stdout + r.stderr


def test_second_implementation_passes():
    """SPEC.md must define the format, not describe one implementation of it.

    `reference/rowspec_alt/` was written from the prose by an author forbidden
    to read `reference/rowspec/`. It is the only evidence the document is
    sufficient -- and it silently drifted 117 cases behind because no test and
    no CI job ran it while §4.1, §4.2 and §9 were being written.
    """
    r = _run("run_cases.py", "rowspec_alt.table")
    assert r.returncode == 0, r.stdout + r.stderr


def test_mutation_gate_is_sound():
    """Assert the gate's own VERDICT, not a substring of its report.

    This asserted `"0 survived" in stdout`, which is true when mutants have
    gone STALE -- their patterns no longer match the source, so they are never
    applied, never survive, and never appear in the survivor count. Six went
    stale and this test stayed green while `just mutants` exited 1 and CI went
    red, which is the precise failure the mutation gate exists to detect,
    occurring in the test that runs it.

    `mutants.py` already decides this correctly and reports it in its exit
    code. Defer to it.
    """
    r = _run("mutants.py")
    assert r.returncode == 0, r.stdout + r.stderr


def _gate_tree(tmp_path):
    """A copy of the gate and what it measures, so a test can plant files in
    it without touching the scratch file of a gate running in this tree."""
    skip = shutil.ignore_patterns("__pycache__", "mutant_impl.py", ".mutants.lock")
    for name in ("conformance", "reference"):
        shutil.copytree(os.path.join(ROOT, name), tmp_path / name, ignore=skip)
    return tmp_path / "conformance"


def test_a_leftover_scratch_file_is_refused_not_overwritten(tmp_path):
    """A run killed mid-probe leaves a MUTATED `mutant_impl.py` behind, and the
    file is gitignored, so nothing else shows it. The next run used to write
    over it and delete it, so the evidence of the kill went with it (#81)."""
    conf = _gate_tree(tmp_path)
    stale = conf / "mutant_impl.py"
    stale.write_text("# left behind by a killed run\n")
    r = subprocess.run(
        [sys.executable, "mutants.py"], cwd=conf, capture_output=True, text=True, timeout=600
    )
    assert r.returncode == 2, f"expected 2, got {r.returncode}\n" + r.stdout[-500:] + r.stderr
    assert str(stale) in r.stderr, r.stderr
    assert stale.read_text() == "# left behind by a killed run\n"


def _start_gate(conf):
    return subprocess.Popen(
        [sys.executable, "mutants.py"],
        cwd=conf,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


def _first_line(p, timeout=30):
    with selectors.DefaultSelector() as sel:
        sel.register(p.stderr, selectors.EVENT_READ)
        return p.stderr.readline() if sel.select(timeout=timeout) else ""


def _await(cond, timeout=60):
    deadline = time.monotonic() + timeout
    while not cond() and time.monotonic() < deadline:
        time.sleep(0.05)
    return cond()


#: How long a gate that should be waiting is watched for NOT proceeding. A
#: gate that does not wait writes its scratch file in well under a second.
WATCH = 3


def test_a_second_run_waits_for_the_one_holding_the_tree(tmp_path):
    """`just test` runs the gate, so `just test` beside `just mutants` is two
    gates writing one scratch file, and each aborted the other (#81).

    Waiting means both halves: it does not touch the scratch file while the
    lock is held, and it does once the lock is released. Saying "waiting" and
    then going ahead anyway passed the first version of this test."""
    conf = _gate_tree(tmp_path)
    scratch = conf / "mutant_impl.py"
    held = open(conf / ".mutants.lock", "a")
    fcntl.flock(held, fcntl.LOCK_EX)
    p = _start_gate(conf)
    try:
        said = _first_line(p)
        assert "waiting for another mutation gate run" in said, said
        time.sleep(WATCH)
        assert p.poll() is None, "exited instead of waiting"
        assert not scratch.exists(), "wrote the scratch file while another run held the tree"
        held.close()
        assert _await(scratch.exists), "never proceeded once the lock was released"
    finally:
        held.close()
        if p.poll() is None:
            p.kill()
            p.communicate()


def test_a_second_run_is_shut_out_while_a_gate_is_measuring(tmp_path):
    """The lock is EXCLUSIVE and held for the whole run, not just taken.

    A shared lock, or one released before the mutants are probed, lets a
    second gate in beside the first, and the second then reads the first
    one's scratch file as a killed run's leftover and refuses (#81)."""
    conf = _gate_tree(tmp_path)
    p = _start_gate(conf)
    try:
        assert _await((conf / "mutant_impl.py").exists), "the gate never started measuring"
        with open(conf / ".mutants.lock", "a") as other:
            with pytest.raises(BlockingIOError):
                fcntl.flock(other, fcntl.LOCK_SH | fcntl.LOCK_NB)
    finally:
        p.kill()
        p.communicate()


def test_a_leftover_is_not_judged_while_another_run_holds_the_tree(tmp_path):
    """While another run holds the lock, the scratch file on disk is ITS
    scratch file, not a leftover. The check must come after the lock, or a
    second gate refuses a run that is alive and well."""
    conf = _gate_tree(tmp_path)
    scratch = conf / "mutant_impl.py"
    scratch.write_text("# the live run's mutant\n")
    held = open(conf / ".mutants.lock", "a")
    fcntl.flock(held, fcntl.LOCK_EX)
    p = _start_gate(conf)
    try:
        said = _first_line(p)
        assert "waiting for another mutation gate run" in said, said
        time.sleep(WATCH)
        assert p.poll() is None, "refused instead of waiting"
        held.close()
        # Released with the file still there: now it IS a leftover.
        _, err = p.communicate(timeout=60)
        assert p.returncode == 2, err
        assert str(scratch) in err, err
    finally:
        held.close()
        if p.poll() is None:
            p.kill()
            p.communicate()


def test_suite_rejects_a_vacuous_implementation():
    """A parser that stores the raw bytes and understands nothing must FAIL.

    `== 1`, not `!= 0`. The runner now has THREE exit codes -- 2 means the
    fixture tree yielded no verdict -- so `!= 0` is satisfied by the suite
    measuring nothing, which is the failure this test exists to detect wearing
    the costume of the test that detects it. Watched: with the tree pointed at
    an empty directory the vacuous implementation exits 2, and `!= 0` passed.
    """
    vac = os.path.join(CONF, "_vacuous.py")
    open(vac, "w").write(
        "import sys, os\n"
        "sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'reference'))\n"
        "from rowspec.table import *\n"
        "def structure(t): return {'raw': t}\n"
        "def render(s): return s['raw']\n"
    )
    try:
        r = _run("run_cases.py", "_vacuous")
        assert r.returncode == 1, (
            "expected exit 1 -- cases FAILED. Exit 2 is 'no verdict from the tree', "
            f"which is not the suite rejecting anything. Got {r.returncode}.\n"
            + r.stdout
            + r.stderr
        )
    finally:
        os.path.exists(vac) and os.remove(vac)


def test_an_unimportable_implementation_is_no_verdict():
    """An implementation that will not import means no case ran: exit 2, the
    runner's no-verdict code, and never 1, which claims a case failed."""
    r = _run("run_cases.py", "no.such.module")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "HARD FAILURE:" in r.stderr, r.stderr
    assert "Traceback" not in r.stderr, r.stderr


@pytest.mark.parametrize("code", [0, 1])
def test_an_implementation_that_exits_on_import_is_no_verdict(code):
    """`sys.exit(0)` during import would otherwise exit 0 -- a pass with no
    case run -- and `sys.exit(1)` would claim a case failed."""
    name = f"_exits_{code}"
    path = os.path.join(CONF, name + ".py")
    with open(path, "w") as fh:
        fh.write(f"import sys\nsys.exit({code})\n")
    try:
        r = _run("run_cases.py", name)
    finally:
        os.remove(path)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "HARD FAILURE:" in r.stderr, r.stderr


def test_help_explains_the_implementation_argument():
    """Every caller passes IMPL first; `--help` must say what it is, and that
    a fixture root given alone would be read as IMPL."""
    r = _run("run_cases.py", "--help")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "IMPL" in r.stdout, r.stdout
    assert "importable module" in r.stdout, r.stdout
    assert "first positional" in r.stdout, r.stdout


def test_a_fixture_root_given_alone_is_refused_not_run_as_impl():
    """`run_cases.py cases` imports the directory as a namespace package and
    fails every case against it -- exit 1, a verdict about nothing."""
    r = _run("run_cases.py", "cases")
    assert r.returncode == 2, r.stdout[-500:] + r.stderr
    assert "is a path, not a module" in r.stderr, r.stderr
