#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Conformance runner driven ENTIRELY by the fixture tree.

It never imports the case definitions. Any implementation exposing the same
five entry points can be checked against the same directory, in any language,
by a runner written in that language.

Everything above that line -- walking the tree, reading fixtures as exact
bytes, dispatching on `kind`, counting what was opened, and refusing to report
success over a tree that yielded no verdict -- is
[kindkit](https://github.com/kindspec/kindkit) and is the same for every kind.
This file is what is left once that is taken out: the handlers that know what
a rowspec case MEANS, and nothing else.

Two profiles, one tree each, because SPEC.md §13 says CSV mode is "a different
profile, not a relaxation", and an implementation claiming it "states which
profile it means":

    --profile mdtbl   cases/       the format itself (the default)
    --profile csv     cases-csv/   an ordinary `.csv`, checked against §13

They are separate roots rather than one tree with a filter so that each root
is run WHOLE. kindkit's `conform.py` refuses a report that leaves any case
under its root unrun, which is right: a run that leaves cases unopened and
reports a pass is how this runner once printed "0 failure(s)" over 226 cases.
So an implementation that claims only
the `.mdtbl` profile runs all of `cases/` and none of `cases-csv/`, and the
skip is the choice of root, stated on its command line.

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

from kindkit import EXIT_NO_VERDICT, Adapter, cli, gitmerge

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "cases")
CSV_CASES = os.path.join(HERE, "cases-csv")

sys.path.insert(0, os.path.join(HERE, "..", "reference"))

#: The tree that shrank, as opposed to the tree that vanished. `discover`
#: already refuses an EMPTY root; this refuses a root that has quietly lost
#: most of itself -- a filter, a bad path, a half-checked-out tree. It is a
#: FLOOR measured with `find conformance/cases -name expect.json | wc -l`, so
#: adding cases never touches it and removing them has to be deliberate.
MIN_CASES = 519

#: The same floor for SPEC.md §13's CSV tree, measured the same way over
#: `conformance/cases-csv`.
MIN_CSV_CASES = 85

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
        if "refusal_contains" in case.expect:
            # The field this one replaced. Ignoring it would let a case written
            # to the old schema assert less than its author meant.
            yield "`refusal_contains` is no longer read; name the §9 identifier in `refusal`"
            return
        try:
            ev_at(ref, case.files["input"], case.dir)
            got = None
        except ref.Malformed as ex:
            # SPEC §9: the identifier is read from the refusal, never parsed
            # out of its message, which each implementation words freely.
            got = getattr(ex, "refusal", None), str(ex)
        if case.expect["accept"]:
            if got is not None:
                yield f"expected accept, got {got[0]!r}: {got[1]!r}"
            return
        want = case.expect.get("refusal")
        if isinstance(want, str):
            want = [want]
        if not want or not all(isinstance(w, str) and w for w in want):
            # A refusal case naming no identifier passes on a refusal for any
            # reason, which is the hole this field exists to close (#61).
            yield f"refusal case names no identifier: refusal={case.expect.get('refusal')!r}"
        elif got is None or got[0] not in want:
            yield f"expected refusal {' or '.join(want)}, got " + (
                "accept" if got is None else f"{got[0]!r}: {got[1]!r}"
            )

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


#: The artifact a CSV-profile case checks. Fixed, like `input.mdtbl`: the case
#: directory is the repository root (cases-csv/README.md), so a sidecar declaring
#: its key is a file beside it, found by the implementation the way it would
#: find one in a real repository. Nothing in `expect.json` names either file.
CSV_INPUT = "input.csv"

#: Every field a CSV-profile `check` case may carry. Anything else is refused
#: rather than ignored: a misspelt `warns` would otherwise be a field nothing
#: checks, in a case that still reports a pass.
CSV_FIELDS = frozenset({"kind", "accept", "refusal_contains", "warns", "warning_contains"})

#: kindkit reads a case's fixtures as UTF-8 text before any handler runs, and a
#: fixture that does not decode is a fault in the whole TREE, not in the case.
#: §9.14 is about bytes that are not well-formed UTF-8, so a CSV case has to be
#: able to hold them, whatever §13 makes of them. The CSV is therefore never registered as a
#: fixture: the handler reads `input.csv` itself, as bytes, and the adapter
#: names a suffix no case file carries.
CSV_NOT_A_FIXTURE = ".kindkit-does-not-read-csv"


def csv_adapter_for(impl):
    """The adapter for SPEC.md §13's CSV profile, checking `impl`.

    `impl` is the CSV-mode module, not the table module: the profiles are
    separate claims and an implementation may make either. Its entry point is
    `check_file(path)`, returning findings whose `level` is `"refuse"` or
    `"warn"` and whose `str()` is the message, and it may raise `Malformed`
    for a file it cannot read at all. A module without both is refused here,
    which `main` turns into exit 2: it does not implement the profile, and
    running the tree against it would be a verdict about nothing.
    """
    mod = importlib.import_module(impl)
    importlib.reload(mod)
    missing = [name for name in ("check_file", "Malformed") if not hasattr(mod, name)]
    if missing:
        raise LookupError(
            f"{impl} has no {' or '.join(missing)}, so it does not implement the CSV "
            "profile (SPEC.md §13)"
        )

    def check(case):
        e = case.expect
        unknown = sorted(set(e) - CSV_FIELDS)
        if unknown:
            yield f"unknown field(s) {unknown}; nothing would check them"
            return
        if not isinstance(e.get("accept"), bool):
            yield "'accept' must be true or false"
            return
        if "warns" in e and e["warns"] is not True:
            # An implementation may emit advisory warnings the spec does not
            # require, so the absence of a warning is not something the spec
            # lets a case assert. `warns: false` would fail a conforming
            # implementation for saying more than §13 asks.
            yield "'warns' may only be true: no warning is not something SPEC.md lets a case check"
            return
        if e["accept"]:
            if "refusal_contains" in e:
                yield "'refusal_contains' on an accepted file; nothing would check it"
                return
            if "warning_contains" in e and e.get("warns") is not True:
                yield "'warning_contains' needs 'warns': true; nothing would check it"
                return
        elif "warns" in e or "warning_contains" in e or "refusal_contains" not in e:
            yield "a refused file asserts 'refusal_contains' and nothing about warnings"
            return
        for name in ("refusal_contains", "warning_contains"):
            if name in e and not isinstance(e[name], str):
                yield f"{name!r} must be a string"
                return

        path = os.path.join(case.dir, CSV_INPUT)
        if not os.path.isfile(path):
            yield f"no {CSV_INPUT} in the case; nothing would have run"
            return
        try:
            findings = list(mod.check_file(path))
        except mod.Malformed as ex:
            refusals, warnings = [str(ex)], []
        else:
            levels = sorted({f.level for f in findings} - {"refuse", "warn"})
            if levels:
                yield f"finding level(s) {levels} are neither 'refuse' nor 'warn'"
                return
            refusals = [str(f) for f in findings if f.level == "refuse"]
            warnings = [str(f) for f in findings if f.level == "warn"]

        if not e["accept"]:
            want = e["refusal_contains"]
            if not any(want in r for r in refusals):
                yield f"expected refusal ~{want!r}, got {refusals or 'no refusal'!r}"
            return
        if refusals:
            yield f"expected accept, got {refusals!r}"
        if e.get("warns") is True:
            want = e.get("warning_contains", "")
            if not any(want in w for w in warnings):
                yield f"expected a warning ~{want!r}, got {warnings or 'no warning'!r}"

    return Adapter(fixture_suffixes=(CSV_NOT_A_FIXTURE,), handlers={"check": check})


#: SPEC.md §13's profiles: the adapter, the implementation checked when none is
#: named, the tree, and its floor.
PROFILES = {
    "mdtbl": (adapter_for, "rowspec.table", CASES, MIN_CASES),
    "csv": (csv_adapter_for, "rowspec.csvmode", CSV_CASES, MIN_CSV_CASES),
}


IMPL_HELP = """\
IMPL is an importable module exposing the entry points the handlers call
(default: rowspec.table, or rowspec.csvmode under `--profile csv`). It is
always the first positional argument, so `run_cases.py ROOT` alone reads ROOT
as IMPL: give a fixture root as `run_cases.py rowspec.table ROOT`.

--profile mdtbl|csv selects SPEC.md §13's profile, and with it the default
tree: cases/ for mdtbl (the default), cases-csv/ for csv.
"""


def take_profile(argv):
    """Split `--profile P` / `--profile=P` out of `argv`: (profile, the rest).

    Taken out BEFORE IMPL is read, so `run_cases.py --profile csv IMPL` still
    reads IMPL as the first positional. Given twice, the run is refused rather
    than resolved: which tree ran must never depend on argument order.
    """
    found, rest, it = [], [], iter(argv)
    for arg in it:
        if arg == "--profile":
            found.append(next(it, ""))
        elif arg.startswith("--profile="):
            found.append(arg.split("=", 1)[1])
        else:
            rest.append(arg)
    if len(found) > 1:
        raise ValueError(f"--profile given {len(found)} times")
    profile = found[0] if found else "mdtbl"
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}; expected one of {sorted(PROFILES)}")
    return profile, rest


def main(argv):
    """`run_cases.py [IMPL] [ROOT] [--profile mdtbl|csv] [--min-cases N]`.

    `IMPL` is an importable module, so the gate can point this at a file it
    has just broken. The fixture root defaults to `cases/` ANCHORED to this
    file, not to the working directory: reading it relatively is how this
    runner once walked an empty path and printed "0 failure(s)" over 226
    unopened cases, four of which were failing.
    """
    try:
        profile, rest = take_profile(argv)
    except ValueError as exc:
        print(f"\nHARD FAILURE: {exc}", file=sys.stderr)
        return EXIT_NO_VERDICT
    build, impl, root, min_cases = PROFILES[profile]
    if rest and not rest[0].startswith("-"):
        impl, rest = rest[0], rest[1:]
    if "-h" in rest or "--help" in rest:
        print(IMPL_HELP)
    if os.path.exists(impl):
        # `run_cases.py cases` would import the directory as a namespace
        # package and fail every case against it: exit 1, a verdict about an
        # "implementation" that is really a fixture root.
        print(
            f"\nHARD FAILURE: IMPL {impl!r} is a path, not a module. IMPL is the first "
            f"positional argument; pass `run_cases.py {PROFILES[profile][1]} {impl}`.",
            file=sys.stderr,
        )
        return EXIT_NO_VERDICT
    try:
        adapter = build(impl)
    except (Exception, SystemExit) as exc:
        # An implementation that will not import means no case ran, which is
        # exit 2. Left uncaught it was Python's default 1: "a case failed" --
        # and a module calling `sys.exit(0)` while importing exited 0, a pass
        # over a suite that never ran. KeyboardInterrupt still propagates.
        print(
            f"\nHARD FAILURE: cannot load the implementation {impl!r}: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return EXIT_NO_VERDICT
    return cli.main(
        adapter,
        rest,
        # IMPL is consumed above, before kindkit builds the parser, so the
        # usage line is the only place `--help` can name it.
        prog="run_cases.py [IMPL] [--profile mdtbl|csv]",
        default_root=root,
        default_min_cases=min_cases,
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
