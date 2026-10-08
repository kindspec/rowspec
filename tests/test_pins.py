# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Every action this repository's CI and its own Action run is pinned to a commit.

A tag can be re-pointed under us, and the release workflow carries the artifact
that reaches PyPI. `docs/ci/` is a template for users and is not covered.

Scanned: every `.github/workflows/*.yml` / `*.yaml`, and every `action.yml` /
`action.yaml` anywhere in the tree (the root Action and any composite action
under a subdirectory). `uses:` is found as a block or flow mapping key, quoted
or not, after YAML comments are stripped -- no YAML parser is a dependency.

Limits: this checks that a ref is a 40-hex commit, not that the commit is the
one the trailing `# vX.Y.Z` comment names, nor that it belongs to the expected
owner rather than a fork.
"""

import os
import re
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__"}
COMMENT = re.compile(r"(^|\s)#.*$", re.M)
USES = re.compile(r"""(?:^|[\s{,-])uses:\s*["']?([^\s"',}]+)""", re.M)
PINNED = re.compile(r"@[0-9a-f]{40}$")


def scanned(root=ROOT):
    """(workflow files, action files) under `root`, as paths relative to it."""
    workflows, actions = [], []
    for dirpath, dirnames, files in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if rel == os.path.join("docs", "ci") or rel.startswith(os.path.join("docs", "ci") + os.sep):
            continue
        for f in files:
            path = os.path.normpath(os.path.join(rel, f))
            if rel == os.path.join(".github", "workflows") and f.endswith((".yml", ".yaml")):
                workflows.append(path)
            elif f in ("action.yml", "action.yaml"):
                actions.append(path)
    return sorted(workflows), sorted(actions)


def unpinned(root=ROOT):
    out = []
    workflows, actions = scanned(root)
    for path in workflows + actions:
        with open(os.path.join(root, path), encoding="utf-8") as fh:
            text = COMMENT.sub(r"\1", fh.read())
        for ref in USES.findall(text):
            if not ref.startswith("./") and not PINNED.search(ref):
                out.append(f"{path}: {ref}")
    return out


def test_the_scan_reads_the_files_it_claims_to():
    workflows, actions = scanned()
    assert os.path.join(".github", "workflows", "release.yml") in workflows
    assert "action.yml" in actions
    with open(os.path.join(ROOT, ".github", "workflows", "release.yml"), encoding="utf-8") as fh:
        assert USES.findall(fh.read()), "release.yml has no `uses:` the scan can see"


def test_every_action_is_pinned_to_a_commit():
    assert unpinned() == []


def test_the_scan_sees_every_shape_a_tag_pin_can_take(tmp_path):
    def write(rel, text):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    sha = "3d3c42e5aac5ba805825da76410c181273ba90b1"
    write(".github/workflows/a.yaml", "steps:\n  - uses: actions/checkout@v4\n")
    write(".github/workflows/b.yml", "steps:\n  - { uses: actions/checkout@v5 }\n")
    write(".github/workflows/c.yml", 'steps:\n  - uses: "actions/checkout@v6"\n')
    write(
        ".github/workflows/d.yml", "jobs:\n  r:\n    uses: org/repo/.github/workflows/x.yml@main\n"
    )
    write(
        ".github/workflows/ok.yml", f"steps:\n  - uses: actions/checkout@{sha} # v7\n  - uses: ./\n"
    )
    write(
        ".github/actions/foo/action.yml", "runs:\n  steps:\n    - uses: actions/setup-python@v5\n"
    )
    write("action.yaml", "runs:\n  steps:\n    - uses: actions/setup-node@v4\n")
    write("docs/ci/template.yml", "steps:\n  - uses: actions/checkout@v4\n")
    write(".github/workflows/e.yml", "# a comment that says uses: actions/checkout@v1\n")
    assert unpinned(str(tmp_path)) == [
        ".github/workflows/a.yaml: actions/checkout@v4",
        ".github/workflows/b.yml: actions/checkout@v5",
        ".github/workflows/c.yml: actions/checkout@v6",
        ".github/workflows/d.yml: org/repo/.github/workflows/x.yml@main",
        ".github/actions/foo/action.yml: actions/setup-python@v5",
        "action.yaml: actions/setup-node@v4",
    ]


# GitHub owner and repository names are case-insensitive, so `KindSpec/KindKit`
# calls the same workflow; matched case-insensitively, or a stale ref spelled
# that way is never compared. The commit stays lowercase hex, as `PINNED` wants.
KINDKIT = re.compile(r"(?i:kindspec/kindkit)(?:\.git)?[@/]")
KINDKIT_SHA = re.compile(r"(?i:kindspec/kindkit)(?:\.git)?(?:/[^\s@]*)?@([0-9a-f]{40})\b")


def kindkit_pin(root=ROOT):
    """The commit the `dev` dependency group pins kindkit to."""
    with open(os.path.join(root, "pyproject.toml"), "rb") as fh:
        dev = tomllib.load(fh)["dependency-groups"]["dev"]
    pins = [m.group(1) for d in dev if (m := KINDKIT_SHA.search(d))]
    assert len(pins) == 1, f"expected one kindkit pin in the dev group, found {dev}"
    return pins[0]


def kindkit_workflow_refs(root=ROOT):
    """`(file, ref)` for every `uses:` of a kindkit workflow, and any that names no commit."""
    out = []
    for path in scanned(root)[0]:
        with open(os.path.join(root, path), encoding="utf-8") as fh:
            text = COMMENT.sub(r"\1", fh.read())
        for ref in USES.findall(text):
            if KINDKIT.search(ref):
                m = KINDKIT_SHA.search(ref)
                out.append((path, m.group(1) if m else ref))
    return out


def test_the_kindkit_workflow_runs_at_the_commit_the_package_is_pinned_to():
    """CI's kindkit gates and the kindkit they drive are the same commit.

    `kind.yml` fetches kindkit's tools at the commit in `uses:`; the runner and
    the gate those tools drive are the package pinned in `pyproject.toml`. Moved
    apart, the workflow checks a report contract the installed kit may not keep.
    """
    refs = kindkit_workflow_refs()
    assert refs, "no workflow calls kindkit's kind.yml; the scan sees nothing to compare"
    pin = kindkit_pin()
    assert [r for r in refs if r[1] != pin] == [], f"the dev group pins kindkit to {pin}"
