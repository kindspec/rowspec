#!/usr/bin/env python3
"""The mutation gate.

A conformance suite that cannot FAIL a deliberately broken implementation is
measuring nothing. Each mutant below is a plausible implementation bug. Every
one MUST be caught by at least one case. A mutant that SURVIVES is a hole in
the suite, and is reported as such.

Patterns are matched on a NORMALISED TOKEN STREAM, not on source bytes -- see
`apply_mutant`. Matching on bytes is how this gate silently died the first
time: `ruff format` rewrote quotes and rewrapped lines, twenty-three patterns
stopped matching, and the gate went on exiting 0 while measuring nothing.

Verified durable against `ruff format` at line-length 60/79/100/120, with
single quotes, with tab indentation, and with magic trailing commas both on
and off. The one known gap: at a line length short enough that ruff must
parenthesise a conditional expression to wrap it, the added parens fall
outside the matched span and splicing produces unbalanced source -- which the
compile check turns into a loud failure, never a silent wrong patch.

A mutant that no longer applies is a HARD FAILURE. So is an ambiguous pattern,
an `EQUIVALENT` claim the suite turns out to refute, an `EQUIVALENT` claim
naming a mutant that no longer exists, and a mutant that leaves the suite
unable to reach any verdict at all.

All of that machinery is now [kindkit](https://github.com/kindspec/kindkit) and
is the same for every kind. What is left here is the part that knows what
`table.py` says: the mutants, the claims that some of them are inert, and the
probe that runs THIS suite against a given file.
"""

import os
import re
import subprocess
import sys

from kindkit import ALL, GateError, Verdict, from_table, gate
from kindkit.cli import EXIT_FAILURES, EXIT_NO_VERDICT, EXIT_OK
from run_cases import MIN_CASES

# Mutations proven to have no observable effect: an earlier fix made the
# mutated line unreachable. A gate cannot distinguish these from suite holes on
# its own, so they are recorded explicitly rather than silently deleted.
#
# These are still APPLIED and still run. An equivalent mutant whose pattern has
# gone stale is just as blind as any other, and an "equivalent" mutant that the
# suite kills is a FALSE equivalence claim -- both are reported as failures.
#
# And so is a claim naming a mutant that is not in MUTANTS. `from_table` below
# refuses the orphan rather than joining past it, which is what closes #37:
# `float-accepts-thousands-separators` outlived the mutant it named, excusing
# nothing, and nothing said so.
EQUIVALENT = {
    "a-missing-column-is-blank-under-a-text-comparison": (
        "§4.2 rule 10's header rule makes this unreachable: `_eval_plain` "
        "resolves every static name against `cols` BEFORE any row is "
        "evaluated, so a name that does not exist never reaches the cell "
        "lookup at all. The mutant is kept rather than deleted because the "
        "lookup is the second of two independent defences and was itself a "
        'live defect once -- `.get(name, "")` returned one sentinel for a '
        'blank cell and a missing column, and `if(nope = "", 1, 0)` fired '
        "the missing-data fallback in every row. The mutant that bites today "
        "is `a-missing-name-is-an-error-only-where-its-branch-is-taken`"
    ),
    "computed-columns-evaluated-in-reverse-header-order": (
        "the plain-formula loop evaluates a column only once its STATIC "
        "dependencies have left `pending`, so a column's value is decided by "
        "the dependency graph and never by the order the loop happens to "
        "visit it in -- which is §4.2 rule 9, and the reason header order is "
        "not an input to any value"
    ),
}

# (old, new) -- or (old, new, ALL) to patch every occurrence rather than
# requiring the pattern to be unique.
MUTANTS = {
    # --- rules added AFTER the first adversarial pass ----------------------
    # Commissioned by the suite author, who could name the case each should die
    # to without being able to write the mutant -- they may not read the
    # implementation. A guard nothing bites is not a guard.
    "signed-drops-the-minus": (
        "            sign = -1.0",
        "            sign = 1.0",
    ),
    "signed-applies-to-the-left-operand": (
        '    a = _number(c.lhs, env)\n    b = c.rhs if c.kind == "num" else _number(c.rhs, env)',
        "    a = -_number(c.lhs, env) if c.rhs < 0 else _number(c.lhs, env)\n"
        '    b = abs(c.rhs) if c.kind == "num" else _number(c.rhs, env)',
    ),
    "signed-strips-the-minus-from-a-string-rhs": (
        '                kind, rhs = "str", v3',
        '                kind, rhs = "str", v3.lstrip("-")',
    ),
    "string-comparison-against-a-computed-column-is-allowed": (
        "        for c in sorted(str_cmp_lhs(t) & computed):",
        "        for c in sorted(frozenset() & computed):",
    ),
    "nine-22-refuses-every-string-comparison": (
        "        for c in sorted(str_cmp_lhs(t) & computed):",
        "        for c in sorted(str_cmp_lhs(t)):",
    ),
    "function-names-match-case-insensitively": (
        '        if name != "if":',
        '        if name.lower() != "if":',
    ),
    "cond-parens-do-not-count-toward-64": (
        "        eat(name)\n        depth += 1",
        "        eat(name)\n        depth += 0",
    ),
    # The natural OVER-correction to the header/data rule: hoist a fault found
    # while evaluating one row to the whole column, which is right for a name
    # that does not resolve and wrong for a division by zero. Commissioned by
    # the suite author, who noted nothing measured the DATA side of that line.
    # --- canon/render terminators, and the header-cell `where` -------------
    # All three reproduce a bug that ACTUALLY happened: the first is the
    # divergence issue #5 reported, the second is a patch that landed in the
    # wrong function, the third is what made issue #7's fixture vacuous.
    "canon-leaves-declaration-terminators-verbatim": (
        '    return "".join(out).replace("\\r\\n", "\\n").replace("\\r", "\\n")',
        '    return "".join(out)',
    ),
    "render-normalises-terminators-like-canon": (
        # Anchored on the line ABOVE the return, which is unique to
        # `render`. The return alone is not: the matcher compares token
        # runs, so `return "".join(out)` is a PREFIX of canon's
        # `return "".join(out).replace(...)` and matches both.
        '    out += st["row_raws"]\n    out += st["tail"]\n    return "".join(out)',
        '    out += st["row_raws"]\n    out += st["tail"]\n'
        '    return "".join(out).replace("\\r\\n", "\\n")',
    ),
    "header-group-call-does-not-require-where": (
        r'_GROUP = re.compile(r"(\w+)\(\s*(\w+)\s+where\s+(.+?)\s*\)\s*$")',
        r'_GROUP = re.compile(r"(\w+)\(\s*(\w+)(?:\s+where\s+(.+?))?\s*\)\s*$")',
    ),
    # --- the four that were LIVE DIVERGENCES between the implementations ----
    # Each restores the behaviour one side actually had. A survivor here means
    # the suite would let that divergence come back.
    "prior-reads-past-a-blank-row": (
        "prev = raw if v is None else v",
        "prev = prev if v is None else v",
    ),
    "cumulative-resumes-after-a-blank": (
        "                    poisoned = True",
        "                    poisoned = poisoned",
    ),
    "order-column-accepts-a-blank-cell": (
        '    if any(v == "" for v in vals):',
        "    if False:",
    ),
    "the-annotation-scan-does-not-skip-strings": (
        "        if m.group().startswith('\"'):",
        "        if False:",
    ),
    "count-coerces-like-the-other-four": (
        '    if fn == "count":\n        return len(vals)',
        "    if False:\n        return len(vals)",
    ),
    # --- §7/§8: an aggregate with no operands -------------------------------
    "empty-min-is-blank": (
        'elif not nums:\n    return "#REF!(empty)"',
        'elif not nums:\n    return ""',
    ),
    "empty-avg-is-zero": (
        'if not nums:\n            return "#REF!(empty)"',
        "if not nums:\n            return 0.0",
    ),
    "the-blank-route-empties-count-too": (
        'if fn == "count":\n    return len(vals)',
        'if fn == "count":\n    return len([v for v in vals if v not in ("", None)])',
    ),
    "ref-empty-is-disambiguated-into-a-sixth-shape": (
        'elif not nums:\n    return "#REF!(empty)"',
        'elif not nums:\n    return f"#REF!(empty:{what})"',
    ),
    # --- §7: an aggregate is defined on the MULTISET ------------------------
    # Each is a reading §7 decided against, and each should die to the case
    # written for it. A rule with a passing suite and no mutant is a rule
    # nothing has tried to break.
    "sum-accumulates-left-to-right": (
        "    if divisor == 1:\n        try:\n            return math.fsum(nums)",
        "    if divisor == 1:\n        try:\n            return sum(nums)",
    ),
    "avg-is-the-rounded-sum-over-count": (
        "        got = _exact(nums, len(nums))",
        "        got = _exact(nums, 1) / len(nums)",
    ),
    "cumulative-uses-the-exact-sum-instead-of-stepping": (
        # ONE mutant, spanning the initialiser through the accumulation:
        # splitting it left half that adds an unused variable (equivalent)
        # and half that references one the other half declares, and
        # mutants are applied one at a time. Rounding `acc + v` once is
        # also not the alternative reading -- that is what a binary64
        # addition already does. The reading §7 rejects is an exact sum
        # over the whole prefix, rounded once at the end.
        """acc, prev, poisoned = 0.0, None, False
for r in seq:
    raw = str(r.get(src, "")).strip()
    try:
        v = num(raw)
    except (ValueError, TypeError):
        v = None
    if fn == "prior":
        r[nm] = "" if prev is None else prev
    elif fn == "delta":
        if prev is None:
            r[nm] = ""
        elif v is None or not isinstance(prev, float):
            r[nm] = f"#REF!({src})"
        else:
            d = v - prev
            r[nm] = "#REF!(overflow)" if d in (INF, -INF) else d
    elif fn == "cumulative":
        if v is None:
            poisoned = True
        if poisoned:
            r[nm] = f"#REF!({src})"
        else:
            acc += v""",
        """acc, prev, poisoned, _seen = 0.0, None, False, []
for r in seq:
    raw = str(r.get(src, "")).strip()
    try:
        v = num(raw)
    except (ValueError, TypeError):
        v = None
    if fn == "prior":
        r[nm] = "" if prev is None else prev
    elif fn == "delta":
        if prev is None:
            r[nm] = ""
        elif v is None or not isinstance(prev, float):
            r[nm] = f"#REF!({src})"
        else:
            d = v - prev
            r[nm] = "#REF!(overflow)" if d in (INF, -INF) else d
    elif fn == "cumulative":
        if v is None:
            poisoned = True
        if poisoned:
            r[nm] = f"#REF!({src})"
        else:
            _seen.append(v)
            acc = _exact(_seen, 1)""",
    ),
    "a-data-fault-is-hoisted-to-the-whole-column-like-a-name-fault": (
        '                except KeyError as e:\n                    r[nm] = f"#REF!({e.args[0]})"',
        "                except KeyError as e:\n"
        '                    r[nm] = f"#REF!({e.args[0]})"\n'
        "                    for _o in seq:\n"
        "                        _o[nm] = r[nm]",
    ),
    "a-missing-name-is-an-error-only-where-its-branch-is-taken": (
        "            miss = [n for n in names if n not in known]",
        "            miss = []",
    ),
    "a-missing-column-is-blank-under-a-text-comparison": (
        "    v = env[name]",
        '    v = env.get(name, "")',
    ),
    # --- §4.2 rule 10, `if` -----------------------------------------------
    # Every one of these is a reading the rule explicitly decided AGAINST, so a
    # survivor is not a missing test in the abstract: it names the [CHOICE] the
    # suite currently takes on faith.
    "if-evaluates-both-branches": (
        "        return ev(node.a, env) if truth(node.c, env) else ev(node.b, env)",
        "        _a, _b = ev(node.a, env), ev(node.b, env)\n"
        "        return _a if truth(node.c, env) else _b",
    ),
    "if-cycle-analysis-follows-only-one-branch": (
        "        names_of(node.a, out)\n        names_of(node.b, out)",
        "        names_of(node.a, out)",
    ),
    "if-comparison-names-are-not-dependencies": (
        '        add(node.c.lhs)\n        if node.c.kind == "name":\n            add(node.c.rhs)',
        "        pass",
    ),
    "if-equality-is-always-numeric": (
        '        if c.kind == "str":',
        "        if False:",
    ),
    "if-equality-is-always-text": (
        "        eq = _number(c.lhs, env) == c.rhs",
        "        eq = str(_cell(c.lhs, env)) == str(c.rhs)",
    ),
    "if-blank-is-loud-even-in-an-equality": (
        "            lv = _cell(c.lhs, env)",
        "            lv = _number(c.lhs, env)",
    ),
    "if-ordering-is-textual-when-both-sides-are-text": (
        '    a = _number(c.lhs, env)\n    b = c.rhs if c.kind == "num" else _number(c.rhs, env)',
        "    try:\n"
        "        a = _number(c.lhs, env)\n"
        '        b = c.rhs if c.kind == "num" else _number(c.rhs, env)\n'
        "    except KeyError:\n"
        "        a, b = str(_cell(c.lhs, env)), str(c.rhs)",
    ),
    "if-is-recognised-with-a-space-before-its-paren": (
        '            if i < len(expr) and expr[i] == "(":',
        '            if expr[i:].lstrip().startswith("("):',
    ),
    "drop-every-third-row": (
        "rows.append(_ANY)",
        "if len(rows) % 3 != 2: rows.append(_ANY)",
    ),
    "ignore-conflict-markers": (
        "if _ANY.startswith(CONFLICT):",
        "if False and _ANY.startswith(CONFLICT):",
    ),
    "allow-duplicate-columns": ("if c in seen:", "if False:"),
    "allow-duplicate-aggregates": ("if name in decls:", "if False:"),
    "allow-duplicate-row-ids": ("if len(set(ids)) != len(ids):", "if False:"),
    "skip-field-count-check": ("if len(v) != len(cols):", "if False:"),
    "ignore-declared-order": (
        'seq = sorted(rows, key=lambda r: (typed(r), str(r.get(key, ""))))',
        "seq = rows",
    ),
    "allow-rowrel-without-order": ("if order is None:", "if False:"),
    "ref-becomes-zero": (
        "if bad:\n    return bad[0]",
        "if bad:\n    return 0.0",
    ),
    "off-by-one-cumulative": (
        'if poisoned:\n    r[nm] = f"#REF!({src})"\nelse:\n    acc += v',
        'if fn == "cumulative":\n    r[nm] = acc\n    acc += v',
    ),
    "render-drops-tail": (
        'out += st["row_raws"]\nout += st["tail"]',
        'out += st["row_raws"]',
    ),
    "render-drops-alignment": (
        'if st["align_raw"]:\n    out.append(st["align_raw"])',
        'if False:\n    out.append(st["align_raw"])',
    ),
    "no-nfc-normalisation": (
        'text = unicodedata.normalize("NFC", text)',
        "text = text",
        ALL,
    ),
    "skip-alignment-check": (
        "if len(split_row(tbl[1])) != len(cols):",
        "if False:",
    ),
    # --- the tiebreak the whole confluence claim rests on -----------------------
    "no-tiebreak-at-all": (
        'seq = sorted(rows, key=lambda r: (typed(r), str(r.get(key, ""))))',
        "seq = sorted(rows, key=lambda r: typed(r))",
    ),
    "tiebreak-reversed": (
        'seq = sorted(rows, key=lambda r: (typed(r), str(r.get(key, ""))))',
        'seq = sorted(rows, key=lambda r: (typed(r), [-ord(ch) for ch in str(r.get(key, ""))]))',
    ),
    "non-numeric-order-sorts-by-id-only": (
        'if kind == "date":\n'
        '    y, m, d = (int(x) for x in re.split(r"[-/]", v))\n'
        "    return (y, m, d)\n"
        "return v",
        'if kind == "date":\n'
        '    y, m, d = (int(x) for x in re.split(r"[-/]", v))\n'
        "    return (y, m, d)\n"
        'return ""',
    ),
    # --- two of the three row-relative operators are never exercised -----------
    "prior-always-blank": (
        'if fn == "prior":\n    r[nm] = "" if prev is None else prev',
        'if fn == "prior":\n    r[nm] = ""',
    ),
    "delta-first-row-is-the-value": (
        'if prev is None:\n    r[nm] = ""\nelif v is None or not isinstance(prev, float):',
        'if False:\n    r[nm] = ""\nelif v is None or not isinstance(prev, float):',
    ),
    "delta-is-negated": (
        "    d = v - prev",
        "    d = prev - v",
    ),
    # --- aggregate functions -----------------------------------------------------
    "count-off-by-one": (
        'if fn == "count":\n    return len(vals)',
        'if fn == "count":\n    return len(vals) - 1',
    ),
    "count-ignores-blanks": (
        'if fn == "count":\n    return len(vals)',
        'if fn == "count":\n    return len([v for v in vals if v not in ("", None)])',
    ),
    "unknown-aggregate-function-silently-becomes-sum": (
        'if fn not in ("sum", "count", "min", "max", "avg"):\n'
        '    raise Malformed(f"unknown aggregate function {fn!r} in {nm!r}")',
        'if fn not in ("sum", "count", "min", "max", "avg"):\n    fn = "sum"',
    ),
    "sum-crashes-on-a-blank-cell": (
        'if fn == "sum":\n    got = _exact(nums, 1)',
        'if fn == "sum":\n    return sum(float(v) for v in vals)',
    ),
    # --- I3's headline promise: a blank cell is NEVER zero ----------------------
    "blank-cell-in-a-real-column-is-zero": (
        '    v = _cell(name, env)\n    if v == "":\n        raise KeyError(name)',
        '    v = _cell(name, env)\n    if v == "":\n        return 0.0',
    ),
    # --- numeric coercion, entirely unspecified and entirely untested -----------
    # was `float-accepts-thousands-separators`; the permissive float() it
    # targeted is gone, replaced by the §4.1 number grammar. The defect worth
    # guarding is now the grammar itself being loosened back to Python's
    # float(), which accepts Arabic-Indic digits, PEP 515 separators and
    # exponents -- all of which §8 requires to be refused.
    "number-grammar-accepts-anything-python-does": (
        "if not isinstance(v, str) or not _NUMBER.match(v):",
        "if not isinstance(v, str):",
    ),
    # The implementation now strips ASCII whitespace only, deliberately, so the
    # defect to guard against inverted: silently eating a non-ASCII space that
    # SPEC §8 requires to become #REF!. Renamed to match what it now tests.
    "strip-eats-non-ascii-spaces": (
        'c.strip(" \t")',
        "c.strip()",
    ),
    # so deleting the explicit .strip(...) would be a no-op. The named
    "computed-columns-evaluated-in-reverse-header-order": (
        "for nm in sorted(pending):",
        "for nm in sorted(pending, reverse=True):",
    ),
    # the two ordering defects that each produced a silent wrong number:
    # a group aggregate over a computed column summed empty cells to 0, and a
    # column depending on cumulative() was #REF!. Both were pass-ordering.
    # The SECOND plain pass. Removing it is what made a per-vendor subtotal over
    # a computed column evaluate to 0 with `check` reporting 0 refused.
    "plain-pass-runs-only-once": (
        "    _eval_plain(seq, plain, computed=frozenset(formulas), "
        "cols=frozenset(cols))\n"
        "    # row-relative, computed over the DERIVED order",
        "    # row-relative, computed over the DERIVED order",
    ),
    # Writes the right value to the WRONG row. Under the old `str(value) in out`
    # check this survived whenever the value already appeared anywhere in the
    # file, which for a small fixture is most of the time.
    "set-cell-writes-to-the-first-matching-row": (
        "if str(r.get(key)) == str(row_key):",
        "if True:",
    ),
    # --- namespaces the suite tests for `key` but not for `order` ---------------
    "allow-duplicate-order-declaration": ("if order_seen:", "if False:"),
    "order-accepts-any-function": (
        'if fn != "by":',
        "if False:",
    ),
    # --- a data row that looks like an alignment row is silently dropped --------
    "is-align-matches-any-dashed-cell": (
        "return bool(cells) and all(_ANY.fullmatch(c) for c in cells)",
        "return bool(cells) and any(_ANY.fullmatch(c) for c in cells)",
    ),
    # --- CONTROLS: these MUST be killed, or the harness is broken ---------------
    "CONTROL-drop-every-third-row": (
        "rows.append(_ANY)",
        "if len(rows) % 3 != 2: rows.append(_ANY)",
    ),
    "CONTROL-render-reverses-rows": (
        "row_raws = [lines[i] for i in tbl_idx[2:]]",
        "row_raws = [lines[i] for i in tbl_idx[2:]][::-1]",
    ),
    "canon-keeps-padding": (
        'return "| " + " | ".join(escape_cell(c) for c in cells) + " |"',
        'return "| " + " | ".join(escape_cell(c).ljust(12) for c in cells) + " |"',
    ),
    # the escape is now the only thing that lets a real value contain a pipe;
    # dropping it silently splits one cell into two
    "render-does-not-escape-pipes": (
        'return "| " + " | ".join(escape_cell(c) for c in cells) + " |"',
        'return "| " + " | ".join(str(c) for c in cells) + " |"',
    ),
    # `render` replays unmodified rows from stored raw lines, so the serialiser
    # is only reachable through `canon`. The path a real EDITOR takes is
    # set_cell, and it is a different function.
    "set-cell-does-not-escape-pipes": (
        'st["row_raws"][i] = "| " + " | ".join(escape_cell(c) for c in cells) + " |\\n"',
        'st["row_raws"][i] = "| " + " | ".join(str(c) for c in cells) + " |\\n"',
    ),
    "unescape-applied-everywhere": (
        'return [unescape_cell(c.strip(" \\t")) for c in _UNESCAPED_PIPE.split(body)]',
        'return [c.strip(" \\t") for c in _UNESCAPED_PIPE.split(body)]',
    ),
    # the carve-out for `count` just moved, so pin it from BOTH sides
    "count-poisons-on-unparseable-text": (
        '    if fn == "count":\n        return len(vals)',
        '    if fn == "count" and all(_isnum(v) for v in vals if v not in ("", None)):\n'
        "        return len(vals)",
    ),
    "count-never-poisons": (
        '    bad = [v for v in vals if isinstance(v, str) and v.startswith("#REF!")]',
        '    bad = [] if fn == "count" else [\n'
        '        v for v in vals if isinstance(v, str) and v.startswith("#REF!")\n'
        "    ]",
    ),
    "canon-drops-formulas": (
        'hdr.append(f"{c} = {st[\'formulas\'][c]}" if c in st["formulas"] else c)',
        "hdr.append(c)",
    ),
    "missing-agg-col-crashes": (
        'if col not in cols:\n    out[nm] = f"#REF!({col})"\n    continue',
        'if False:\n    out[nm] = f"#REF!({col})"\n    continue',
    ),
}


# ---------------------------------------------------------------------------
# The probe: run THIS suite against a given file and say what it found.
#
# Everything below the mutant table is rowspec-specific and nothing above it
# is. The kit splices, hashes, purges bytecode and accounts for the verdicts;
# it has no idea that the thing being run is a fixture tree of tables.
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
IMPL = os.path.normpath(os.path.join(HERE, "..", "reference", "rowspec", "table.py"))
RUNNER = os.path.join(HERE, "run_cases.py")

#: A name NOTHING ELSE on the path claims. `sys.path[0]` is the directory of
#: the script the probe runs -- this one -- and the first matching directory
#: wins, so a leftover module of the same name anywhere on the path would
#: shadow the file the gate is measuring. The kit refuses to let this be the
#: implementation itself: the scratch file is overwritten and then deleted.
SCRATCH = os.path.join(HERE, "mutant_impl.py")

_FAIL = re.compile(r"\s+FAIL (\S+)")
_TOTAL = re.compile(r"(\d+) failure\(s\) across (\d+) case\(s\) in the fixture tree")

#: Seconds a single probe may take. The whole tree runs in about two, so this
#: is two orders of magnitude of headroom and only a mutant that made the suite
#: LOOP could reach it -- `drop-every-third-row` is one line away from being
#: that mutant. Without it the gate hangs until CI's job timeout kills it, and
#: a hang is the one outcome that carries no verdict at all while looking, from
#: the outside, exactly like a slow one.
PROBE_TIMEOUT = 300


def probe(path):
    """Case ids the fixture tree reports as failing for the module in `path`.

    A SET, not a count. The reference itself need not pass every case -- the
    suite is written adversarially and runs ahead of the implementation -- so
    "the mutant made N cases fail" proves nothing. A mutant is killed only if
    it breaks a case that passes WITHOUT it.

    And a set is not enough on its own. This function used to add a
    `<runner crashed>` sentinel to the set when the runner produced no
    accounting, which made "the suite never ran" indistinguishable from "every
    case that ran said no" -- a mutant that stopped `table.py` importing was
    scored `killed` with not one case opened (#45). `reached=False` is the
    honest answer, and the kit reports it as BROKEN rather than as a kill.

    `reached` is decided from what the run PRODUCED, not from what it
    intended: the exit code has to be one of the two that mean a verdict, the
    accounting line has to be there, it has to account for at least the whole
    tree, and it has to agree with the FAIL lines printed above it. A run
    missing any of those measured something other than this suite -- and a run
    that never finishes is the same finding, reached by waiting.
    """
    module = os.path.splitext(os.path.basename(path))[0]
    # cwd=HERE and every path anchored to __file__. This file used to read
    # `../reference/...` relative to wherever the gate was started, and
    # `run_cases.py` had the same shape once and printed "0 failure(s)" over
    # 226 cases it had never opened, four of them failing.
    try:
        run = subprocess.run(
            [sys.executable, RUNNER, module],
            capture_output=True,
            text=True,
            cwd=HERE,
            timeout=PROBE_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        # Not a kill, and not a survivor. The suite never finished, so it never
        # said anything -- which is the same finding as a crash, and BROKEN is
        # already the name for it.
        return Verdict(reached=False)
    ids, shown, total = set(), 0, None
    for line in run.stdout.splitlines():
        hit = _FAIL.match(line)
        if hit:
            ids.add(hit.group(1))
            shown += 1
            continue
        hit = _TOTAL.search(line)
        if hit:
            total = (int(hit.group(1)), int(hit.group(2)))
    if run.returncode not in (EXIT_OK, EXIT_FAILURES) or total is None:
        return Verdict(reached=False)  # it crashed, or it found no tree to walk
    failures, cases = total
    if cases < MIN_CASES or failures != shown:
        # It ran, but not over this tree, or its own accounting disagrees with
        # what it printed. Either way the verdict is not about these 410 cases.
        return Verdict(reached=False)
    return Verdict(ids)


def main():
    """Three exit codes, the same three the runner uses and for the same reason.

    A gate that could not run is not a gate that found nothing: an orphaned
    equivalence claim, a scratch path pointing at the implementation, or a
    suite that reaches no verdict on the UNMUTATED source all mean every
    number this run could print would be meaningless.
    """
    try:
        report = gate(
            source=IMPL,
            mutants=from_table(MUTANTS, EQUIVALENT),
            probe=probe,
            scratch=SCRATCH,
        )
    except GateError as exc:
        print(f"\nHARD FAILURE: {exc}", file=sys.stderr)
        return EXIT_NO_VERDICT
    return EXIT_OK if report.ok else EXIT_FAILURES


if __name__ == "__main__":
    sys.exit(main())
