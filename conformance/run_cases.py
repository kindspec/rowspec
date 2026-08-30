#!/usr/bin/env python3
"""Conformance runner driven ENTIRELY by the fixture tree.

It never imports the case definitions. Any implementation exposing the same
five entry points can be checked against the same directory, in any language,
by a runner written in that language.
"""

import importlib
import inspect
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reference"))


def sh(*a, cwd=None):
    return subprocess.run(a, cwd=cwd, capture_output=True, text=True)


def git_merge(files, order, fn="a.mdtbl"):
    d = tempfile.mkdtemp()
    try:
        if sh("git", "init", "-q", d).returncode:
            raise RuntimeError("git init failed: merge cases cannot be run")
        for k, v in [
            ("user.email", "t@e"),
            ("user.name", "t"),
            # Git's background auto-maintenance writes `maintenance.lock` into
            # the repo and outlives the command that triggered it, so it races
            # the `rmtree` below and the case dies with a FileNotFoundError
            # naming a file no fixture contains. Observed on a CI runner, never
            # reproduced locally in 5 consecutive runs. Nothing here needs
            # maintenance: these repos exist for one merge and are deleted.
            ("gc.auto", "0"),
            ("maintenance.auto", "false"),
        ]:
            sh("git", "config", k, v, cwd=d)
        p = os.path.join(d, fn)
        open(p, "w").write(files["base"])
        sh("git", "add", "-A", cwd=d)
        if sh("git", "commit", "-qm", "b", cwd=d).returncode:
            raise RuntimeError("git commit failed: merge cases cannot be run")
        sh("git", "branch", "-M", "main", cwd=d)
        for i, name in enumerate(order):
            sh("git", "checkout", "-q", "main", cwd=d)
            sh("git", "checkout", "-qb", f"b{i}", cwd=d)
            open(p, "w").write(files[name])
            if sh("git", "commit", "-qam", name, cwd=d).returncode:
                raise RuntimeError(f"git commit failed on branch {name}")
        sh("git", "checkout", "-q", "main", cwd=d)
        for i in range(len(order)):
            if sh("git", "merge", f"b{i}", "-m", "m", cwd=d).returncode:
                return "conflict", open(p).read()
        return "clean", open(p).read()
    finally:
        # Failing to delete a temp directory must never fail a conformance
        # case: the merge already happened and its outcome is already read.
        shutil.rmtree(d, ignore_errors=True)


def ev_at(ref, text, base):
    """Evaluate `text` as if it were the artifact sitting in `base`.

    SPEC §7's `lookup(other.mdtbl, ...)` is a path resolved relative to the
    REFERRING artifact, so an evaluator that is handed only bytes cannot
    resolve one. The case directory is that artifact's directory -- and, by
    the convention in cases/README.md, its repository root -- so companion
    artifacts are ordinary files sitting beside `input.mdtbl`. No new
    `expect.json` field is needed: the tree itself carries the second table.

    An implementation whose `evaluate` takes no base is called without one.
    That is a real answer, not an excuse: it will report every lookup as
    unresolved and FAIL the cases that resolve, which is the signal wanted.
    """
    if len(inspect.signature(ref.evaluate).parameters) > 1:
        return ref.evaluate(text, base)
    return ref.evaluate(text)


KINDS = {
    "parse",
    "roundtrip",
    "eval",
    "rowrel",
    "mutate",
    "canon",
    "merge",
    "confluence",
}
CANON_CHECKS = {"idempotent", "preserves-values", "removes-padding", "already-canonical"}


def run(impl, root="cases"):
    ref = importlib.import_module(impl)
    importlib.reload(ref)
    fails = []
    seen = 0
    for dirpath, _, names in sorted(os.walk(root)):
        if "expect.json" not in names:
            continue
        seen += 1
        cid = os.path.relpath(dirpath, root)
        e = json.load(open(os.path.join(dirpath, "expect.json")))
        f = {
            n.split(".")[0]: open(os.path.join(dirpath, n), encoding="utf-8", newline="").read()
            for n in names
            if n.endswith(".mdtbl")
        }
        k = e["kind"]

        def bad(msg, cid=cid):
            fails.append(f"{cid}: {msg}")
            print(f"  FAIL {cid}  {msg}")

        if k not in KINDS:
            bad(f"unknown kind {k!r}; nothing would have run")
            continue
        if k == "eval" and not e.get("aggregates"):
            bad("eval case asserts no aggregate")
            continue
        if k == "canon" and e["check"] not in CANON_CHECKS:
            bad(f"unknown canon check {e['check']!r}; nothing would have run")
            continue

        try:
            if k == "parse":
                try:
                    ev_at(ref, f["input"], dirpath)
                    got = None
                except ref.Malformed as ex:
                    got = str(ex)
                if e["accept"] and got is not None:
                    bad(f"expected accept, got {got!r}")
                elif not e["accept"] and (got is None or e["refusal_contains"] not in got):
                    bad(f"expected refusal ~{e['refusal_contains']!r}, got {got!r}")
            elif k == "roundtrip":
                out = ref.render(ref.structure(f["input"]))
                if out != f["input"]:
                    bad(f"{len(f['input'])}B in, {len(out)}B out")
            elif k == "eval":
                _, a = ev_at(ref, f["input"], dirpath)
                for kk, vv in e["aggregates"].items():
                    if a.get(kk) != vv:
                        bad(f"{kk}: wanted {vv!r}, got {a.get(kk)!r}")
            elif k == "rowrel":
                rows, _ = ev_at(ref, f["input"], dirpath)
                got = rows[e["row_index"]].get(e["column"])
                if got != e["value"]:
                    bad(f"{e['column']}: wanted {e['value']!r}, got {got!r}")
            elif k == "mutate":
                st = ref.structure(f["input"])
                rk = e["row_key"]
                if e.get("expect") == "refuse":
                    try:
                        ref.set_cell(st, rk, e["column"], e["value"])
                        bad("accepted a computed-cell write")
                    except ref.Malformed:
                        pass
                else:
                    out = ref.render(ref.set_cell(st, rk, e["column"], e["value"]))
                    if "aggregate" in e:
                        _, a = ev_at(ref, out, dirpath)
                        if a.get(e["aggregate"]) != e["result"]:
                            bad(
                                f"wanted {e['aggregate']}={e['result']}, "
                                f"got {a.get(e['aggregate'])}"
                            )
                    else:
                        # Not `str(value) in out`: a substring test over the whole
                        # file passes when the value already appears anywhere in
                        # it, including in the row that was NOT written.
                        rows_out, _ = ev_at(ref, out, dirpath)
                        hit = [r for r in rows_out if rk in r.values()]
                        if not hit:
                            bad(f"row {rk!r} is gone from the rendered output")
                        elif str(hit[0].get(e["column"])) != str(e["value"]):
                            bad(
                                f"{e['column']} of row {rk}: wanted {e['value']!r}, "
                                f"got {hit[0].get(e['column'])!r}"
                            )
            elif k == "canon":
                c1 = ref.canon(f["input"])
                c2 = ref.canon(c1)
                if e["check"] == "idempotent" and c1 != c2:
                    bad("canon not idempotent")
                elif (
                    e["check"] == "preserves-values"
                    and ev_at(ref, f["input"], dirpath)[1] != ev_at(ref, c1, dirpath)[1]
                ):
                    bad("canon changed the values")
                elif e["check"] == "removes-padding":
                    body = [ln for ln in c1.splitlines() if ln.startswith("|")]
                    padded = [
                        ln
                        for ln in body
                        if re.search(r"\|  +[^ |]", ln) or re.search(r"[^ |]  +\|", ln)
                    ]
                    if padded:
                        bad(f"alignment padding survived canon: {padded[0]!r}")
                    elif c1 == f["input"] and any("  " in ln for ln in f["input"].splitlines()):
                        bad("canon is the identity function on padded input")
                elif e["check"] == "already-canonical" and c1 != f["input"]:
                    bad("canon changed canonical input")
            elif k == "merge":
                st, merged = git_merge(f, ["ours", "theirs"])
                if st != e["git_outcome"]:
                    bad(f"git said {st}, expected {e['git_outcome']}")
                elif e.get("then") == "refuse":
                    try:
                        ev_at(ref, merged, dirpath)
                        bad("parser ACCEPTED a corrupt merge")
                    except ref.Malformed:
                        pass
                elif e.get("then") == "evaluate":
                    _, a = ev_at(ref, merged, dirpath)
                    for kk, vv in e["aggregates"].items():
                        if a.get(kk) != vv:
                            bad(f"SILENTLY WRONG: {kk} wanted {vv}, got {a.get(kk)}")
            elif k == "confluence":
                names = [f"branch{i}" for i in range(e["branches"])]
                res = set()
                for perm in itertools.permutations(names):
                    s2, m2 = git_merge(f, list(perm))
                    res.add(
                        "conflict"
                        if s2 == "conflict"
                        else tuple(sorted(ev_at(ref, m2, dirpath)[1].items()))
                    )
                if len(res) != 1:
                    bad(f"{len(res)} distinct outcomes across merge orders")
        except Exception as ex:
            bad(f"{type(ex).__name__}: {ex}")
    if not seen:
        # A suite that finds no cases must not report success. `root` is
        # relative, so running this from the repo root instead of `conformance/`
        # walked an empty path and printed "0 failure(s)" over 226 unrun cases
        # -- four of which were failing.
        fails.append(f"no cases found under {os.path.abspath(root)!r}")
        print(f"  FAIL no cases found under {os.path.abspath(root)!r}")
    return fails


if __name__ == "__main__":
    f = run(sys.argv[1] if len(sys.argv) > 1 else "rowspec.table")
    print(f"\n{len(f)} failure(s) across the fixture tree")
    sys.exit(1 if f else 0)
