"""Every action this repository's CI and its own Action run is pinned to a commit.

A tag can be re-pointed under us, and the release workflow carries the artifact
that reaches PyPI. `docs/ci/` is a template for users and is not covered.
"""

import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USES = re.compile(r"^\s*-?\s*uses:\s*(\S+)", re.M)
PINNED = re.compile(r"@[0-9a-f]{40}$")


def files():
    return sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))) + [
        os.path.join(ROOT, "action.yml")
    ]


def unpinned():
    out = []
    for path in files():
        with open(path, encoding="utf-8") as fh:
            for ref in USES.findall(fh.read()):
                if not ref.startswith("./") and not PINNED.search(ref):
                    out.append(f"{os.path.relpath(path, ROOT)}: {ref}")
    return out


def test_the_scan_reads_the_files_it_claims_to():
    found = {os.path.relpath(p, ROOT) for p in files()}
    assert {".github/workflows/release.yml", "action.yml"} <= found
    with open(os.path.join(ROOT, ".github", "workflows", "release.yml"), encoding="utf-8") as fh:
        assert USES.findall(fh.read()), "release.yml has no `uses:` the scan can see"


def test_every_action_is_pinned_to_a_commit():
    assert unpinned() == []
