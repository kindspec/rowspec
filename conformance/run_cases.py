#!/usr/bin/env python3
"""Conformance runner driven ENTIRELY by the fixture tree.

It never imports the case definitions. Any implementation exposing the same
five entry points can be checked against the same directory, in any language,
by a runner written in that language.
"""

import importlib
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
        sh("git", "init", "-q", d)
        for k, v in [("user.email", "t@e"), ("user.name", "t")]:
            sh("git", "config", k, v, cwd=d)
        p = os.path.join(d, fn)
        open(p, "w").write(files["base"])
        sh("git", "add", "-A", cwd=d)
        sh("git", "commit", "-qm", "b", cwd=d)
        sh("git", "branch", "-M", "main", cwd=d)
        for i, name in enumerate(order):
            sh("git", "checkout", "-q", "main", cwd=d)
            sh("git", "checkout", "-qb", f"b{i}", cwd=d)
            open(p, "w").write(files[name])
            sh("git", "commit", "-qam", name, cwd=d)
        sh("git", "checkout", "-q", "main", cwd=d)
        for i in range(len(order)):
            if sh("git", "merge", f"b{i}", "-m", "m", cwd=d).returncode:
                return "conflict", open(p).read()
        return "clean", open(p).read()
    finally:
        shutil.rmtree(d)


def run(impl, root="cases"):
    ref = importlib.import_module(impl)
    importlib.reload(ref)
    fails = []
    for dirpath, _, names in sorted(os.walk(root)):
        if "expect.json" not in names:
            continue
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

        try:
            if k == "parse":
                try:
                    ref.evaluate(f["input"])
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
                _, a = ref.evaluate(f["input"])
                for kk, vv in e["aggregates"].items():
                    if a.get(kk) != vv:
                        bad(f"{kk}: wanted {vv!r}, got {a.get(kk)!r}")
            elif k == "rowrel":
                rows, _ = ref.evaluate(f["input"])
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
                        _, a = ref.evaluate(out)
                        if a.get(e["aggregate"]) != e["result"]:
                            bad(
                                f"wanted {e['aggregate']}={e['result']}, "
                                f"got {a.get(e['aggregate'])}"
                            )
                    elif str(e["value"]) not in out:
                        bad("mutation not visible")
            elif k == "canon":
                c1 = ref.canon(f["input"])
                c2 = ref.canon(c1)
                if "idempotent" in e["check"] and c1 != c2:
                    bad("canon not idempotent")
                elif (
                    e["check"] == "preserves-values"
                    and ref.evaluate(f["input"])[1] != ref.evaluate(c1)[1]
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
                        ref.evaluate(merged)
                        bad("parser ACCEPTED a corrupt merge")
                    except ref.Malformed:
                        pass
                elif e.get("then") == "evaluate":
                    _, a = ref.evaluate(merged)
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
                        else tuple(sorted(ref.evaluate(m2)[1].items()))
                    )
                if len(res) != 1:
                    bad(f"{len(res)} distinct outcomes across merge orders")
        except Exception as ex:
            bad(f"{type(ex).__name__}: {ex}")
    return fails


if __name__ == "__main__":
    f = run(sys.argv[1] if len(sys.argv) > 1 else "rowspec.table")
    print(f"\n{len(f)} failure(s) across the fixture tree")
    sys.exit(1 if f else 0)
