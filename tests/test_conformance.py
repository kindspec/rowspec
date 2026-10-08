# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The conformance suite and the mutation gate, as tests.

The suite is the deliverable; running it under pytest is a convenience, not the
definition. `just conform` runs the same cases directly.
"""

import os
import subprocess
import sys

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
