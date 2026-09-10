#!/usr/bin/env python3
"""Conformance runner driven ENTIRELY by the fixture tree.

It never imports the case definitions. Any implementation exposing the same
five entry points can be checked against the same directory, in any language,
by a runner written in that language.

Everything above that line -- walking the tree, reading fixtures as exact
bytes, dispatching on `kind`, counting what was opened, and refusing to report
success over a tree that yielded no verdict -- is
[kindkit](https://github.com/kindspec/kindkit) and is the same for every kind.
This file is what is left once that is taken out: the eight handlers that know
what a rowspec case MEANS, and nothing else.

Three exit codes, not two, because "every case passed" and "no case ran" must
never look alike from the outside:

    0   every case passed
    1   at least one case failed -- a verdict about the implementation
    2   the fixture tree yielded no verdict at all
"""

import importlib
import inspect
import itertools
import os
import re
import sys

from kindkit import Adapter, cli, gitmerge

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "cases")

sys.path.insert(0, os.path.join(HERE, "..", "reference"))

#: The tree that shrank, as opposed to the tree that vanished. `discover`
#: already refuses an EMPTY root; this refuses a root that has quietly lost
#: most of itself -- a filter, a bad path, a half-checked-out tree. It is a
#: FLOOR measured with `find conformance/cases -name expect.json | wc -l`, so
#: adding cases never touches it and removing them has to be deliberate.
MIN_CASES = 410

CANON_CHECKS = {"idempotent", "preserves-values", "removes-padding", "already-canonical"}

#: The merge cases file their sides under fixed stems, and the artifact is
#: always one file. Which stem is the base and which are the branches is
#: rowspec's filing convention, which is why the kit is handed texts.
ARTIFACT = "a.mdtbl"


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


def merge_sides(case, order):
    """Run stock git over the case's sides, in `order`, and report what it did."""
    return gitmerge.merge(case.files["base"], [case.files[n] for n in order], ARTIFACT)


def adapter_for(impl):
    """Build the adapter that checks `impl` -- the ONE thing the kit is told.

    The implementation module is a parameter rather than a constant because
    the same tree checks three of them: `rowspec.table`, the independent
    `rowspec_alt.table`, and whatever file the mutation gate has just broken.
    """
    ref = importlib.import_module(impl)
    importlib.reload(ref)

    def parse(case):
        try:
            ev_at(ref, case.files["input"], case.dir)
            got = None
        except ref.Malformed as ex:
            got = str(ex)
        if case.expect["accept"] and got is not None:
            yield f"expected accept, got {got!r}"
        elif not case.expect["accept"] and (
            got is None or case.expect["refusal_contains"] not in got
        ):
            yield f"expected refusal ~{case.expect['refusal_contains']!r}, got {got!r}"

    def roundtrip(case):
        out = ref.render(ref.structure(case.files["input"]))
        if out != case.files["input"]:
            yield f"{len(case.files['input'])}B in, {len(out)}B out"

    def eval_(case):
        e = case.expect
        if not e.get("aggregates"):
            # A case that asserts nothing cannot fail, and a suite of them
            # reports a number that means nothing.
            yield "eval case asserts no aggregate"
            return
        _, a = ev_at(ref, case.files["input"], case.dir)
        for kk, vv in e["aggregates"].items():
            if a.get(kk) != vv:
                yield f"{kk}: wanted {vv!r}, got {a.get(kk)!r}"

    def rowrel(case):
        e = case.expect
        rows, _ = ev_at(ref, case.files["input"], case.dir)
        got = rows[e["row_index"]].get(e["column"])
        if got != e["value"]:
            yield f"{e['column']}: wanted {e['value']!r}, got {got!r}"

    def mutate(case):
        e = case.expect
        st = ref.structure(case.files["input"])
        rk = e["row_key"]
        if e.get("expect") == "refuse":
            try:
                ref.set_cell(st, rk, e["column"], e["value"])
                yield "accepted a computed-cell write"
            except ref.Malformed:
                pass
            return
        out = ref.render(ref.set_cell(st, rk, e["column"], e["value"]))
        if "aggregate" in e:
            _, a = ev_at(ref, out, case.dir)
            if a.get(e["aggregate"]) != e["result"]:
                yield f"wanted {e['aggregate']}={e['result']}, got {a.get(e['aggregate'])}"
            return
        # Not `str(value) in out`: a substring test over the whole file passes
        # when the value already appears anywhere in it, including in the row
        # that was NOT written.
        rows_out, _ = ev_at(ref, out, case.dir)
        hit = [r for r in rows_out if rk in r.values()]
        if not hit:
            yield f"row {rk!r} is gone from the rendered output"
        elif str(hit[0].get(e["column"])) != str(e["value"]):
            yield (
                f"{e['column']} of row {rk}: wanted {e['value']!r}, got {hit[0].get(e['column'])!r}"
            )

    def canon(case):
        e = case.expect
        if e["check"] not in CANON_CHECKS:
            yield f"unknown canon check {e['check']!r}; nothing would have run"
            return
        c1 = ref.canon(case.files["input"])
        c2 = ref.canon(c1)
        if e["check"] == "idempotent" and c1 != c2:
            yield "canon not idempotent"
        elif (
            e["check"] == "preserves-values"
            and ev_at(ref, case.files["input"], case.dir)[1] != ev_at(ref, c1, case.dir)[1]
        ):
            yield "canon changed the values"
        elif e["check"] == "removes-padding":
            body = [ln for ln in c1.splitlines() if ln.startswith("|")]
            padded = [
                ln for ln in body if re.search(r"\|  +[^ |]", ln) or re.search(r"[^ |]  +\|", ln)
            ]
            if padded:
                yield f"alignment padding survived canon: {padded[0]!r}"
            elif c1 == case.files["input"] and any(
                "  " in ln for ln in case.files["input"].splitlines()
            ):
                yield "canon is the identity function on padded input"
        elif e["check"] == "already-canonical" and c1 != case.files["input"]:
            yield "canon changed canonical input"

    def merge(case):
        e = case.expect
        st, merged = merge_sides(case, ["ours", "theirs"])
        if st != e["git_outcome"]:
            yield f"git said {st}, expected {e['git_outcome']}"
        elif e.get("then") == "refuse":
            try:
                ev_at(ref, merged, case.dir)
                yield "parser ACCEPTED a corrupt merge"
            except ref.Malformed:
                pass
        elif e.get("then") == "evaluate":
            _, a = ev_at(ref, merged, case.dir)
            for kk, vv in e["aggregates"].items():
                if a.get(kk) != vv:
                    yield f"SILENTLY WRONG: {kk} wanted {vv}, got {a.get(kk)}"

    def confluence(case):
        names = [f"branch{i}" for i in range(case.expect["branches"])]
        res = set()
        for perm in itertools.permutations(names):
            s2, m2 = merge_sides(case, list(perm))
            res.add(
                gitmerge.CONFLICT
                if s2 == gitmerge.CONFLICT
                else tuple(sorted(ev_at(ref, m2, case.dir)[1].items()))
            )
        if len(res) != 1:
            yield f"{len(res)} distinct outcomes across merge orders"

    return Adapter(
        fixture_suffixes=(".mdtbl",),
        handlers={
            "parse": parse,
            "roundtrip": roundtrip,
            "eval": eval_,
            "rowrel": rowrel,
            "mutate": mutate,
            "canon": canon,
            "merge": merge,
            "confluence": confluence,
        },
    )


def main(argv):
    """`run_cases.py [IMPL] [ROOT] [--min-cases N]`.

    `IMPL` is an importable module, so the gate can point this at a file it
    has just broken. The fixture root defaults to `cases/` ANCHORED to this
    file, not to the working directory: reading it relatively is how this
    runner once walked an empty path and printed "0 failure(s)" over 226
    unopened cases, four of which were failing.
    """
    impl, rest = "rowspec.table", list(argv)
    if rest and not rest[0].startswith("-"):
        impl, rest = rest[0], rest[1:]
    return cli.main(
        adapter_for(impl),
        rest,
        prog="run_cases.py",
        default_root=CASES,
        default_min_cases=MIN_CASES,
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
