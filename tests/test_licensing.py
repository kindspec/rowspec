# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The per-directory licence split in LICENSE is true of the tree.

LICENSE says each directory carries its own LICENSE file and source files carry
SPDX headers. Both halves are checked here, because a licence file describing a
practice the repository does not follow is the one place a false claim is
expensive (#42).

Fixtures under conformance/cases/ carry no header: they are exact bytes, and
`.json` cannot hold a comment. That directory's LICENSE is what covers them.
"""

import fnmatch
import os
import re
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPDX = re.compile(r"SPDX-License-Identifier: (.+?)(?: -->)?$")

# The split in LICENSE, and AGENTS.md §6 in the org contract.
DIRECTORIES = {
    "docs": "CC-BY-4.0",
    "conformance/cases": "CC0-1.0",
    # Fixtures for features this edition reserves; fixtures are CC0 so they can
    # be vendored, wherever in the tree they sit.
    "conformance/reserved": "CC0-1.0",
    "conformance": "MIT",
    "reference": "Apache-2.0 OR MIT",
    "export": "Apache-2.0 OR MIT",
    "tests": "Apache-2.0 OR MIT",
}


def tracked():
    """The files git tracks. Not a filesystem glob: an untracked leftover --
    `conformance/_vacuous.py` from an interrupted `just test`, say -- is not
    part of the repository and must not decide this test."""
    try:
        out = subprocess.run(
            ["git", "-C", ROOT, "ls-files", "-z"], capture_output=True, text=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout (e.g. an unpacked sdist): nothing says what is tracked")
    return [p for p in out.split("\0") if p]


def headed_files():
    """{path relative to ROOT: the licence its header must name}."""
    files = tracked()
    want = {"SPEC.md": "CC-BY-4.0"}
    for p in files:
        top = p.split("/", 1)[0]
        if p in ("action.yml", "action.yaml", "justfile") or fnmatch.fnmatch(
            p, ".github/workflows/*.y*ml"
        ):
            # Build and CI configuration: licensed like the code it builds.
            want[p] = "Apache-2.0 OR MIT"
        elif p == "docs/ci/rowspec-check.yml":
            # The copy-me CI template: CC0 so a user can paste it into their
            # repository without an attribution obligation.
            want[p] = "CC0-1.0"
        elif fnmatch.fnmatch(p, "conformance/*.py") and p.count("/") == 1:
            want[p] = "MIT"
        elif fnmatch.fnmatch(p, "conformance/reserved/*.md"):
            want[p] = "CC0-1.0"
        elif top in ("docs", "reference", "export", "tests") and p.endswith((".py", ".md", ".yml")):
            want[p] = DIRECTORIES[top]
    return want


def header(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        for line in fh.read().splitlines()[:3]:
            m = SPDX.search(line)
            if m:
                return m.group(1)
    return None


def test_the_scan_reads_the_files_it_claims_to():
    found = headed_files()
    for p in (
        "SPEC.md",
        "conformance/run_cases.py",
        "action.yml",
        "justfile",
        ".github/workflows/check.yml",
        "docs/ci/rowspec-check.yml",
        "conformance/reserved/README.md",
        "reference/rowspec/table.py",
        "tests/test_licensing.py",
    ):
        assert p in found, p


def test_every_source_file_carries_its_directory_spdx_header():
    wrong = {p: header(p) for p, want in headed_files().items() if header(p) != want}
    assert wrong == {}, f"missing or wrong SPDX header (path: what it says): {wrong}"


def test_every_licensed_directory_carries_a_license_file():
    for d, spdx in DIRECTORIES.items():
        path = os.path.join(ROOT, d, "LICENSE")
        assert os.path.isfile(path), f"{d}/LICENSE is missing"
        with open(path, encoding="utf-8") as fh:
            # The whole identifier: `MIT-0` must not pass for `MIT`.
            text = fh.read()
            assert re.match(re.escape(spdx) + r"(?=$|\s|\.\s)", text), (
                f"{d}/LICENSE does not name {spdx}: {text.splitlines()[0]!r}"
            )
