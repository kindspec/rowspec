# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The per-directory licence split in LICENSE is true of the tree.

LICENSE says each directory carries its own LICENSE file and source files carry
SPDX headers. Both halves are checked here, because a licence file describing a
practice the repository does not follow is the one place a false claim is
expensive (#42).

Fixtures under conformance/cases/ carry no header: they are exact bytes, and
`.json` cannot hold a comment. That directory's LICENSE is what covers them.
"""

import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPDX = re.compile(r"SPDX-License-Identifier: (.+?)(?: -->)?$")

# The split in LICENSE, and AGENTS.md §6 in the org contract.
DIRECTORIES = {
    "docs": "CC-BY-4.0",
    "conformance/cases": "CC0-1.0",
    "conformance": "MIT",
    "reference": "Apache-2.0 OR MIT",
    "export": "Apache-2.0 OR MIT",
    "tests": "Apache-2.0 OR MIT",
}


def headed_files():
    """{path relative to ROOT: the licence its header must name}."""
    want = {"SPEC.md": "CC-BY-4.0"}
    want |= {p: "MIT" for p in glob.glob("conformance/*.py", root_dir=ROOT)}
    for top in ("docs", "reference", "export", "tests"):
        for ext in ("py", "md", "yml"):
            for p in glob.glob(f"{top}/**/*.{ext}", root_dir=ROOT, recursive=True):
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
            assert fh.read().startswith(spdx), f"{d}/LICENSE does not name {spdx}"
