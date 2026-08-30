"""The conformance suite, the mutation gate, and the corpus checks, as tests.

The suite is the deliverable; running it under pytest is a convenience, not the
definition. `just conform` runs the same cases directly.
"""

import os
import subprocess
import sys

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


def test_mutation_gate_has_no_survivors():
    r = _run("mutants.py")
    assert "0 survived" in r.stdout, r.stdout + r.stderr


def test_suite_rejects_a_vacuous_implementation():
    """A parser that stores the raw bytes and understands nothing must FAIL."""
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
        assert r.returncode != 0, "the suite accepted an implementation that understands nothing"
    finally:
        os.path.exists(vac) and os.remove(vac)
