# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The runner's CSV profile (SPEC.md §13, #63), driven against built trees.

These are tests of the RUNNER: what a `check` case asserts, and when a run is
no verdict. They use a stub implementation whose findings are spelled out in
its input, so a verdict here says nothing about any CSV implementation, and
nothing here is a conformance case -- those live in conformance/cases-csv/
and are written from SPEC.md by someone else.
"""

import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF = os.path.join(ROOT, "conformance")

#: Each line of `input.csv` the stub understands becomes one finding, so a
#: case can be built with exactly the outcome a test needs. Anything else,
#: including bytes that are not UTF-8, is data and is ignored.
STUB = """
import os


class Malformed(Exception):
    pass


class Finding:
    def __init__(self, level, message):
        self.level, self.message = level, message

    def __str__(self):
        return self.message


def check_file(path):
    out = []
    if os.path.exists(path + ".rowspec.json"):
        out.append(Finding("warn", "sidecar beside the file"))
    for line in open(path, "rb").read().split(b"\\n"):
        word, _, rest = line.partition(b" ")
        if word == b"MALFORMED":
            raise Malformed(rest.decode())
        if word == b"REFUSE":
            out.append(Finding("refuse", rest.decode()))
        if word == b"WARN":
            out.append(Finding("warn", rest.decode()))
        if word == b"LEVEL":
            out.append(Finding(rest.decode(), "a finding of another level"))
    return out
"""


def refuse(contains, **more):
    return {"accept": False, "refusal_contains": contains, **more}


def accept(**more):
    return {"accept": True, **more}


PASS, FAIL = True, False

#: (case name, input.csv bytes or None for no file, expect.json, passes)
CASES = [
    ("refused-as-expected", b"REFUSE duplicate column\n", refuse("duplicate"), PASS),
    ("refused-for-any-reason", b"REFUSE anything\n", refuse(""), PASS),
    ("unreadable-is-a-refusal", b"MALFORMED no table\n", refuse("no table"), PASS),
    ("one-of-several-matches", b"REFUSE first\nREFUSE second\n", refuse("second"), PASS),
    ("refused-for-another-reason", b"REFUSE duplicate column\n", refuse("key"), FAIL),
    ("accepted-when-refusal-expected", b"a,b\n1,2\n", refuse(""), FAIL),
    ("a-warning-is-not-a-refusal", b"WARN lone CR\n", refuse(""), FAIL),
    ("refused-when-accept-expected", b"REFUSE duplicate column\n", accept(), FAIL),
    ("accepted", b"a,b\n1,2\n", accept(), PASS),
    ("accepted-warnings-unasserted", b"WARN byte-order mark\n", accept(), PASS),
    ("warned-as-expected", b"WARN BOM\n", accept(warns=True, warning_contains="BOM"), PASS),
    ("warned-for-any-reason", b"WARN byte-order mark\n", accept(warns=True), PASS),
    ("warned-for-another-reason", b"WARN BOM\n", accept(warns=True, warning_contains="CR"), FAIL),
    ("no-warning-when-one-expected", b"a,b\n", accept(warns=True), FAIL),
    ("warns-false-is-not-assertable", b"a,b\n", accept(warns=False), FAIL),
    ("bytes-that-are-not-utf8", b"\xff\xfe\xc3(,a\n", accept(), PASS),
    ("a-misspelt-field", b"a,b\n", accept(warn=False), FAIL),
    ("refusal-contains-on-an-accept", b"a,b\n", accept(refusal_contains=""), FAIL),
    ("warning-contains-without-warns", b"WARN x\n", accept(warning_contains="x"), FAIL),
    ("warns-on-a-refusal", b"REFUSE x\n", refuse("", warns=True), FAIL),
    ("refusal-without-refusal-contains", b"REFUSE x\n", {"accept": False}, FAIL),
    ("accept-is-not-a-boolean", b"a,b\n", {"accept": "yes"}, FAIL),
    ("warns-is-not-a-boolean", b"WARN x\n", accept(warns=1), FAIL),
    ("refusal-contains-is-not-a-string", b"REFUSE 1\n", refuse(1), FAIL),
    ("a-finding-of-another-level", b"LEVEL error\n", accept(), FAIL),
    ("no-input-csv", None, accept(), FAIL),
]  # fmt: skip


def _tree(root, cases):
    for name, data, expect, _ in cases:
        d = root / name
        d.mkdir(parents=True)
        (d / "expect.json").write_text(json.dumps({"kind": "check", **expect}))
        if data is None:
            (d / "WHY.md").write_text("a case with no input.csv\n")
        else:
            (d / "input.csv").write_bytes(data)
    return root


def _stub(tmp_path):
    lib = tmp_path / "lib"
    lib.mkdir()
    (lib / "_stub_csvmode.py").write_text(STUB)
    return str(lib)


#: The trees built here are a few cases each, far below the real tree's floor
#: (`MIN_CSV_CASES`), which would otherwise refuse every one of them.
SMALL_TREE = ("--min-cases", "1")


def _run(*args, pythonpath=None):
    env = dict(os.environ)
    if pythonpath:
        env["PYTHONPATH"] = pythonpath + os.pathsep + env.get("PYTHONPATH", "")
    env.pop("KINDKIT_REPORT_JSON", None)
    return subprocess.run(
        [sys.executable, "run_cases.py", *args], cwd=CONF, capture_output=True, text=True, env=env
    )


def test_each_check_case_passes_or_fails_as_it_should(tmp_path):
    root = _tree(tmp_path / "tree", CASES)
    report = tmp_path / "report.json"
    r = _run(
        "_stub_csvmode",
        str(root),
        "--profile",
        "csv",
        "--report-json",
        str(report),
        *SMALL_TREE,
        pythonpath=_stub(tmp_path),
    )
    assert r.returncode == 1, r.stdout + r.stderr
    got = json.loads(report.read_text())
    assert sorted(got["cases"]) == sorted(name for name, *_ in CASES)
    failed = {f["id"] for f in got["failures"]}
    wrong = {name for name, *_, passes in CASES if passes == (name in failed)}
    assert wrong == set(), f"cases whose verdict is wrong: {sorted(wrong)}\n{r.stdout}"


def test_a_sidecar_beside_the_csv_reaches_the_implementation(tmp_path):
    """The case directory is the repository root, so a sidecar is the file
    beside `input.csv`. The runner passes the path; the stub warns when it
    finds the sidecar there, so the same case passes with the sidecar and
    fails once it is gone."""
    cases = [("with", b"a\n", accept(warns=True, warning_contains="sidecar"), PASS)]
    root = _tree(tmp_path / "tree", cases)
    sidecar = root / "with" / "input.csv.rowspec.json"
    sidecar.write_text('{"key": "a"}')
    lib = _stub(tmp_path)
    r = _run("_stub_csvmode", str(root), "--profile", "csv", *SMALL_TREE, pythonpath=lib)
    assert r.returncode == 0, r.stdout + r.stderr
    sidecar.unlink()
    r = _run("_stub_csvmode", str(root), "--profile", "csv", *SMALL_TREE, pythonpath=lib)
    assert r.returncode == 1, r.stdout + r.stderr


def test_the_reference_csv_mode_is_bound(tmp_path):
    """`rowspec.csvmode` is the default CSV implementation and is reachable
    through the profile, in both directions: an empty file is refused, a
    header-only file is not."""
    cases = [
        ("refused", b"", {"accept": False, "refusal_contains": ""}, True),
        ("accepted", b"a,b\n", {"accept": True}, True),
    ]
    root = _tree(tmp_path / "tree", cases)
    r = _run("--profile", "csv", "rowspec.csvmode", str(root), *SMALL_TREE)
    assert r.returncode == 0, r.stdout + r.stderr
    (root / "accepted" / "expect.json").write_text(
        json.dumps({"kind": "check", "accept": False, "refusal_contains": ""})
    )
    r = _run("--profile", "csv", "rowspec.csvmode", str(root), *SMALL_TREE)
    assert r.returncode == 1, r.stdout + r.stderr


def test_the_second_implementation_does_not_claim_the_csv_profile(tmp_path):
    """rowspec_alt implements the .mdtbl profile only (#63). Asked to run a
    CSV tree that HAS cases, it must reach no verdict -- exit 2 -- rather than
    pass them or fail them. The tree is populated so that the exit is about
    the implementation and not about an empty root."""
    root = _tree(tmp_path / "tree", CASES[:1])
    r = _run("rowspec_alt.table", str(root), "--profile", "csv", *SMALL_TREE)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "does not implement the CSV profile" in r.stderr, r.stderr


def test_a_csv_tree_below_its_floor_is_no_verdict(tmp_path):
    """The CSV profile carries a case-count floor like the .mdtbl one, so a
    tree that quietly lost most of itself is no verdict rather than a pass."""
    root = _tree(tmp_path / "tree", [c for c in CASES if c[3]][:1])
    r = _run("_stub_csvmode", str(root), "--profile", "csv", pythonpath=_stub(tmp_path))
    assert r.returncode == 2, r.stdout + r.stderr
    assert "expected at least" in r.stderr, r.stderr


def test_a_case_with_no_input_csv_fails_on_the_guard_not_on_a_crash(tmp_path):
    """The case fails because the runner says it has nothing to run, not
    because the implementation was handed a path that does not exist. A stub
    that crashes on the missing file would fail the case too, so the message
    is what shows the guard ran."""
    root = _tree(tmp_path / "tree", [("no-input-csv", None, accept(), FAIL)])
    report = tmp_path / "report.json"
    r = _run(
        "_stub_csvmode",
        str(root),
        "--profile",
        "csv",
        "--report-json",
        str(report),
        *SMALL_TREE,
        pythonpath=_stub(tmp_path),
    )
    assert r.returncode == 1, r.stdout + r.stderr
    [failure] = json.loads(report.read_text())["failures"]
    assert failure["message"] == "no input.csv in the case; nothing would have run", failure


def test_the_csv_profile_defaults_to_csvmode_over_the_csv_tree(tmp_path):
    """`--profile csv` alone reads conformance/cases-csv/, and passes it: an
    implementation without the CSV entry point exits 2 there, not 0."""
    report = tmp_path / "report.json"
    r = _run("--profile", "csv", "--report-json", str(report))
    assert r.returncode == 0, r.stdout + r.stderr
    got = json.loads(report.read_text())
    assert os.path.realpath(got["root"]) == os.path.realpath(os.path.join(CONF, "cases-csv"))
    assert got["cases"], got


def test_an_empty_csv_tree_is_no_verdict(tmp_path):
    (tmp_path / "empty").mkdir()
    r = _run(
        "_stub_csvmode", str(tmp_path / "empty"), "--profile", "csv", pythonpath=_stub(tmp_path)
    )
    assert r.returncode == 2, r.stdout + r.stderr
    assert "no cases found" in r.stderr, r.stderr


@pytest.mark.parametrize(
    "args, why",
    [
        (("--profile", "xlsx"), "unknown profile 'xlsx'"),
        (("--profile",), "unknown profile ''"),
        (("--profile", "csv", "--profile", "mdtbl"), "--profile given 2 times"),
        (("--profile=mdtbl", "--profile=mdtbl"), "--profile given 2 times"),
    ],
)
def test_a_profile_that_is_not_exactly_one_known_name_is_refused(args, why):
    """Refused for THAT reason. Exit 2 alone is also what the empty CSV tree
    gives, so without the message a doubled `--profile` that silently took
    the first one passed this test (watched)."""
    r = _run(*args)
    assert r.returncode == 2, r.stdout + r.stderr
    assert f"HARD FAILURE: {why}" in r.stderr, r.stderr
    assert "Traceback" not in r.stderr, r.stderr
