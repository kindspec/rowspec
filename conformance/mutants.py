#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
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

import fcntl
import hashlib
import os
import sys

from kindkit import ALL, GateError, MutantError, apply_mutant, from_table, gate, probe_command
from kindkit.cli import EXIT_FAILURES, EXIT_NO_VERDICT, EXIT_OK

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
        "if poisoned is None and (v is None or ovf):",
        "poisoned = None\nif v is None or ovf:",
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
        '    if fn != "count":\n        for v in vals:',
        "    if True:\n        for v in vals:",
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
        """acc, prev, poisoned = 0.0, None, None
prev_ovf = False
prev_err = None
for r in seq:
    raw = str(r.get(src, "")).strip()
    try:
        v = num(raw)
    except (ValueError, TypeError):
        v = None
    ovf = v in (INF, -INF)
    if src in formulas and raw.startswith("#REF!"):
        err = raw
    elif ovf:
        err = "#REF!(overflow)"
    elif v is None:
        err = f"#REF!({src})"
    else:
        err = None
    if fn == "prior":
        if prev is None:
            r[nm] = ""
        else:
            r[nm] = "#REF!(overflow)" if prev_ovf else prev
    elif fn == "delta":
        if prev is None:
            r[nm] = ""
        elif err or prev_err:
            r[nm] = err or prev_err
        else:
            d = v - prev
            r[nm] = "#REF!(overflow)" if d in (INF, -INF) else d
    elif fn == "cumulative":
        if poisoned is None and (v is None or ovf):
            poisoned = "#REF!(overflow)" if ovf else f"#REF!({src})"
        if poisoned:
            r[nm] = poisoned
        else:
            acc += v""",
        """acc, prev, poisoned, _seen = 0.0, None, None, []
prev_ovf = False
prev_err = None
for r in seq:
    raw = str(r.get(src, "")).strip()
    try:
        v = num(raw)
    except (ValueError, TypeError):
        v = None
    ovf = v in (INF, -INF)
    if src in formulas and raw.startswith("#REF!"):
        err = raw
    elif ovf:
        err = "#REF!(overflow)"
    elif v is None:
        err = f"#REF!({src})"
    else:
        err = None
    if fn == "prior":
        if prev is None:
            r[nm] = ""
        else:
            r[nm] = "#REF!(overflow)" if prev_ovf else prev
    elif fn == "delta":
        if prev is None:
            r[nm] = ""
        elif err or prev_err:
            r[nm] = err or prev_err
        else:
            d = v - prev
            r[nm] = "#REF!(overflow)" if d in (INF, -INF) else d
    elif fn == "cumulative":
        if poisoned is None and (v is None or ovf):
            poisoned = "#REF!(overflow)" if ovf else f"#REF!({src})"
        if poisoned:
            r[nm] = poisoned
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
        "if bad:\n    return _first_ref(bad)",
        "if bad:\n    return 0.0",
    ),
    "off-by-one-cumulative": (
        "if poisoned:\n    r[nm] = poisoned\nelse:\n    acc += v",
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
        'if fn == "prior":\n'
        "    if prev is None:\n"
        '        r[nm] = ""\n'
        "    else:\n"
        '        r[nm] = "#REF!(overflow)" if prev_ovf else prev',
        'if fn == "prior":\n    r[nm] = ""',
    ),
    "delta-first-row-is-the-value": (
        'if prev is None:\n    r[nm] = ""\nelif err or prev_err:',
        "if prev is None:\n    r[nm] = err or v\nelif err or prev_err:",
    ),
    "delta-is-negated": (
        "    d = v - prev",
        "    d = prev - v",
    ),
    # --- §9 identifiers (#61): refusing is not enough, it must be for the reason
    # SPEC.md names. Both survive a suite that asserts only THAT a file is refused.
    "every-refusal-reports-one-identifier": (
        "        self.refusal = refusal",
        '        self.refusal = "malformed-formula"',
    ),
    "a-missing-order-is-reported-as-a-bad-order-column": (
        'refusal="rowrel-without-order"',
        'refusal="bad-order-column"',
    ),
    # --- aggregate functions -----------------------------------------------------
    "count-off-by-one": (
        'if fn == "count":\n    return len(vals)',
        'if fn == "count":\n    return len(vals) - 1',
    ),
    "unknown-aggregate-function-silently-becomes-sum": (
        'if fn not in ("sum", "count", "min", "max", "avg"):\n'
        '    raise Malformed(f"unknown aggregate function {fn!r} in {nm!r}", '
        'refusal="unknown-aggregate")',
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
    # A control must break something no other mutant touches, or it cannot
    # fail on its own: this one was a verbatim copy of `drop-every-third-row`.
    "CONTROL-parse-reverses-every-row": (
        "row = dict(zip(cols, v, strict=False))",
        "row = dict(zip(cols, v[::-1], strict=False))",
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
    # --- §8 overflow, §9.12 key, and the §8 order of a predicate's errors ----
    # Each undoes one fix. Most restore what the reference did before it;
    # a-predicate-reports-its-last-unknown-name is instead a plausible way to
    # get the leftmost rule wrong, since the old code stopped at the first
    # unknown name. The same fixes' other guards have no mutant here yet: the tree does not kill
    # one, so each waits, as CSV_MUTANTS' survivors did, for a case from an
    # author who has not read table.py.
    #
    # Only min and max die to a wrong value; sum and avg die by raising.
    "an-infinite-aggregate-operand-is-passed-on": (
        "            if not math.isfinite(x):",
        "            if False:",
    ),
    "a-header-group-aggregate-over-a-missing-column-is-refused": (
        "    if col not in cols:\n        missing = col",
        "    if col not in cols:\n"
        '        raise Malformed(f"column {nm!r} aggregates unknown column {col!r}", '
        'refusal="malformed-formula")',
    ),
    "a-predicate-stops-at-its-first-unknown-name": (
        "                unknown = unknown or c",
        "                raise KeyError(c)",
    ),
    "a-key-naming-no-column-is-accepted": (
        "        if key not in cols:",
        "        if False:",
    ),
    "a-key-naming-a-computed-column-is-accepted": (
        "        if key in formulas:",
        "        if False:",
    ),
    "an-infinite-cell-is-a-number-in-a-row-expression": (
        '    if got in (INF, -INF):\n        raise KeyError("overflow")\n    return got',
        "    return got",
    ),
    "prior-of-an-infinite-cell-is-the-infinity": (
        '            r[nm] = "#REF!(overflow)" if prev_ovf else prev',
        "            r[nm] = prev",
    ),
    "a-predicate-reports-its-last-unknown-name": (
        "                unknown = unknown or c",
        "                unknown = c",
    ),
    "a-group-predicate-waits-on-its-source": (
        "            try:\n"
        "                preds, missing = _predicate(ptext, cols, formulas, "
        '"malformed-formula"), None\n'
        "            except KeyError as e:\n"
        "                preds, missing = None, e.args[0]\n"
        "            if col not in cols:\n"
        "                missing = col\n"
        '            elif col in formulas and any(r.get(col) in (None, "") for r in seq):\n'
        "                continue",
        '            if col in formulas and any(r.get(col) in (None, "") for r in seq):\n'
        "                continue\n"
        "            try:\n"
        "                preds, missing = _predicate(ptext, cols, formulas, "
        '"malformed-formula"), None\n'
        "            except KeyError as e:\n"
        "                preds, missing = None, e.args[0]\n"
        "            if col not in cols:\n"
        "                missing = col",
    ),
    "a-declaration-over-a-missing-column-skips-its-refusals": (
        "    for nm, (fn, col, pred) in decls.items():\n"
        '        if fn not in ("sum", "count", "min", "max", "avg"):',
        "    for nm, (fn, col, pred) in decls.items():\n"
        "        if col not in cols:\n"
        '            out[nm] = f"#REF!({col})"\n'
        "            continue\n"
        '        if fn not in ("sum", "count", "min", "max", "avg"):',
    ),
    "cumulative-is-poisoned-only-by-a-blank": (
        "if poisoned is None and (v is None or ovf):",
        "if poisoned is None and v is None:",
    ),
}


# The CSV profile's own table: deliberate defects in `csvmode.py`, each of which
# SPEC.md §13's case tree (conformance/cases-csv/) must catch. Run with
# `--profile csv`; see TARGETS below.
#
# A mutant the CSV tree does not kill is a hole, as for the table above. The
# ones that survived when this table was first written waited, ungated, until
# a second author wrote cases from the spec for them (kindspec/rowspec#94); they
# are the section below marked as such. A new survivor goes the same way: it
# waits in an issue's text, written in spec terms, until a case from someone
# who has not read csvmode.py kills it, and then it joins this table.
CSV_EQUIVALENT = {
    "csv-empty-file-check-removed": (
        "an empty or whitespace-only file then reaches the header check, which "
        "refuses it as 'no table' too -- a different message for the same refusal, "
        "and §9 makes which diagnostic is reported unobservable"
    ),
    "csv-grouped-header-disabled": (
        "a grouped header has repeated names, so with the shape check off it is "
        "refused as duplicate columns instead -- the same file refused, under §9's "
        "unobservable choice of diagnostic. Not quite true today: where the only "
        "repeated name is empty (`,,,,,a`) the original crashes and the mutant "
        "refuses, which is kindspec/rowspec#92. Re-check this claim when #92 is fixed"
    ),
}

CSV_MUTANTS = {
    # --- §9.1 / §4.1.12: conflict markers --------------------------------------
    "csv-conflict-markers-ignored": (
        "        if not _MARKER.match(line):\n            continue",
        "        if True:\n            continue",
    ),
    "csv-bare-equals-run-is-not-a-marker": (
        r'_MARKER = re.compile(r"^(<{7}|>{7}|\|{7}|={7})")',
        r'_MARKER = re.compile(r"^(<{7}|>{7}|\|{7})")',
    ),
    # --- §13 / RFC 4180: record boundaries -----------------------------------
    "csv-open-quote-at-eof-accepted": (
        "    if opened is not None:",
        "    if False:",
    ),
    "csv-quote-scan-ignores-the-delimiter": (
        '        elif ch == delimiter or ch in "\\r\\n":',
        '        elif ch in "\\r\\n":',
    ),
    "csv-blank-line-between-rows-is-skipped": (
        '    body = [r if r else [""] for r in rest]',
        "    body = [r for r in rest if r]",
    ),
    # --- §9.6: field count -----------------------------------------------------
    "csv-field-count-unchecked": (
        "    ragged = [(i, r) for i, r in enumerate(body, 1) if len(r) != len(header)]",
        "    ragged = []",
    ),
    # --- §3 / §9.14 / §9.26 / §13: encoding ---------------------------------
    "csv-invalid-utf8-is-replaced": (
        '        text = raw.decode("utf-8")',
        '        text = raw.decode("utf-8", "replace")',
    ),
    "csv-bom-is-not-stripped": (
        "        raw = raw[3:]",
        "        raw = raw",
    ),
    "csv-bom-is-not-a-warning": (
        '    if raw.startswith(b"\\xef\\xbb\\xbf"):',
        "    if False:",
    ),
    "csv-lone-cr-is-not-a-warning": (
        '    if "\\r" in text.replace("\\r\\n", ""):',
        "    if False:",
    ),
    # --- §9.2 / §3 / §13: column names ---------------------------------------
    "csv-column-names-not-nfc": (
        '    names = [unicodedata.normalize("NFC", h.strip(" \\t")) for h in header]',
        '    names = [h.strip(" \\t") for h in header]',
    ),
    "csv-duplicate-columns-allowed": (
        "        if len(idxs) == 1:\n            continue",
        "        if True:\n            continue",
    ),
    "csv-cf-in-a-column-name-allowed": (
        '        for ch in name:\n            if unicodedata.category(ch) == "Cf":',
        "        for ch in name:\n            if False:",
    ),
    # --- §9.5 / §9.16 / §13: the declared key ----------------------------------
    "csv-key-on-the-first-column-whatever-is-declared": (
        "        key_idx = names.index(side.key)",
        "        key_idx = 0",
    ),
    "csv-duplicate-keys-unchecked": (
        "        findings += _duplicate_keys(body, names, key_idx)",
        "        pass",
    ),
    "csv-duplicate-keys-not-nfc": (
        '        groups.setdefault(unicodedata.normalize("NFC", raw), []).append((n, raw))',
        "        groups.setdefault(raw, []).append((n, raw))",
    ),
    "csv-empty-key-allowed": (
        '        if raw == "":\n            bad.append(',
        "        if False:\n            bad.append(",
    ),
    "csv-whitespace-in-a-key-allowed": (
        '            if ch.isspace() or unicodedata.category(ch) == "Cf":',
        '            if unicodedata.category(ch) == "Cf":',
    ),
    "csv-cf-in-a-key-allowed": (
        '            if ch.isspace() or unicodedata.category(ch) == "Cf":',
        "            if ch.isspace():",
    ),
    # Gated once stray quotes became a refusal (#96): closing a field
    # at a doubled quote now leaves a stray quote behind it, which the
    # doubled-quote cases see.
    "csv-doubled-quote-closes-the-field": (
        "                if text[i + 1 : i + 2] == '\"':",
        "                if False:",
    ),
    # --- refused either way: see CSV_EQUIVALENT ------------------------------
    "csv-empty-file-check-removed": (
        "    if not raw.strip():",
        "    if False:",
    ),
    "csv-grouped-header-disabled": (
        "        grouped = _grouped_header(names, second)",
        "        grouped = None",
    ),
    "csv-header-only-file-is-no-table": (
        "    if not records or not any(any(c.strip() for c in r) for r in records[:1]):",
        "    if len(records) < 2 or not any(any(c.strip() for c in r) for r in records[:1]):",
    ),
    "csv-sidecar-key-naming-no-column-is-ignored": (
        "        if side.key not in names:",
        "        if False:",
    ),
    # --- killed by the cases written for #94 ---------------------------------
    "csv-key-trim-strips-all-whitespace": (
        '        raw = unicodedata.normalize("NFC", rec[key_idx].strip(" \\t"))',
        '        raw = unicodedata.normalize("NFC", rec[key_idx].strip())',
    ),
    "csv-quote-opens-mid-field": (
        "        elif at_start and ch == '\"':",
        "        elif ch == '\"':",
    ),
    "csv-quote-scan-ignores-a-lone-cr": (
        '        elif ch == delimiter or ch in "\\r\\n":',
        '        elif ch == delimiter or ch == "\\n":',
    ),
    "csv-trailing-empty-line-refused": (
        "    rest = records[1:-1] if len(records) > 1 and records[-1] == [] else records[1:]",
        "    rest = records[1:]",
    ),
    "csv-every-trailing-empty-line-dropped": (
        "    rest = records[1:-1] if len(records) > 1 and records[-1] == [] else records[1:]",
        "    rest = records[1:]\n    while rest and rest[-1] == []:\n        rest = rest[:-1]",
    ),
    "csv-stray-quotes-unchecked": (
        "    if stray:",
        "    if False:",
    ),
    "csv-quote-inside-an-unquoted-field-allowed": (
        "            if (closed or ch == '\"') and (not stray or stray[-1] != start):",
        "            if closed and (not stray or stray[-1] != start):",
    ),
    "csv-text-after-a-closing-quote-allowed": (
        "            if (closed or ch == '\"') and (not stray or stray[-1] != start):",
        "            if ch == '\"' and (not stray or stray[-1] != start):",
    ),
    "csv-marker-after-leading-space": (
        "        if not _MARKER.match(line):\n            continue",
        "        if not _MARKER.match(line.lstrip()):\n            continue",
    ),
    "csv-marker-needs-space-or-end-of-line": (
        r'_MARKER = re.compile(r"^(<{7}|>{7}|\|{7}|={7})")',
        r'_MARKER = re.compile(r"^(<{7}|>{7}|\|{7}|={7})(?: |$)")',
    ),
    # --- CONTROL: must be killed, or the CSV harness is broken ----------------
    "CONTROL-csv-reports-nothing": (
        "    return findings + warnings",
        "    return []",
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

#: A name NOTHING ELSE on the path claims. The first matching directory wins,
#: and `run_cases.py` puts `reference/` ahead of its own directory, so a
#: leftover `mutant_impl.py` under `reference/` would shadow the file the gate
#: is measuring -- silently, and in the direction where every mutant survives.
#: The kit refuses to let this be the implementation itself: the scratch file
#: is overwritten and then deleted.
SCRATCH = os.path.join(HERE, "mutant_impl.py")

#: The CSV profile's target: `csvmode.py`, probed through `run_cases.py
#: --profile csv`. Its scratch name is its own, for SCRATCH's reason, and
#: `csvmode.py` imports `rowspec.table` and `rowspec.sidecar` absolutely so a
#: copy of it outside the package still loads.
CSV_IMPL = os.path.normpath(os.path.join(HERE, "..", "reference", "rowspec", "csvmode.py"))
CSV_SCRATCH = os.path.join(HERE, "mutant_csvmode.py")

#: `--profile` -> (source, mutants, equivalence claims, scratch file, the
#: runner's profile arguments). Each profile is its own gate run with its own
#: report, because kindkit's `check_gate.py` requires a gate report's baseline
#: to have run exactly the tree it names, and the two profiles are two trees.
TARGETS = {
    "mdtbl": (IMPL, MUTANTS, EQUIVALENT, SCRATCH, ()),
    "csv": (CSV_IMPL, CSV_MUTANTS, CSV_EQUIVALENT, CSV_SCRATCH, ("--profile", "csv")),
}

#: Held for the whole run, so two gates in one tree take turns at `SCRATCH`
#: instead of writing over each other's mutants. `just test` runs the gate
#: too, so `just test` beside `just mutants` was two gates on one file, and
#: each aborted the other (#81). An flock dies with its process, so a killed
#: run never leaves the tree locked -- and while it is held, a `SCRATCH` on
#: disk can only be what a killed run left behind.
LOCK = os.path.join(HERE, ".mutants.lock")

#: Seconds a single probe may take. The whole tree runs in about two, so this
#: is two orders of magnitude of headroom and only a mutant that made the suite
#: LOOP could reach it -- `drop-every-third-row` is one line away from being
#: that mutant. Without it the gate hangs until CI's job timeout kills it, and
#: a hang is the one outcome that carries no verdict at all while looking, from
#: the outside, exactly like a slow one.
PROBE_TIMEOUT = 300


def probe(path, profile_args=()):
    """What the fixture tree ran, and which of those cases failed, for `path`.

    A SET of failing ids, not a count. The reference itself need not pass every
    case -- the suite is written adversarially and runs ahead of the
    implementation -- so "the mutant made N cases fail" proves nothing. A
    mutant is killed only if it breaks a case that passes WITHOUT it.

    And the set of cases that RAN, which is what "the suite reached a verdict"
    is decided from. This probe once added a `<runner crashed>` sentinel to the
    failing set when the runner produced no accounting, scoring a mutant that
    stopped `table.py` importing as `killed` with not one case opened (#45).
    The kit now refuses a failing id that did not run.

    `probe_command` reads the runner's `--report-json` rather than its printed
    summary, so nothing here parses prose. No report, an exit code other than
    0 or 1, a report the exit code contradicts, or a run that outlasts
    `PROBE_TIMEOUT` is no verdict -- BROKEN, never a kill. A tree that shrank
    below `MIN_CASES` is the runner's own exit 2.
    """
    module = os.path.splitext(os.path.basename(path))[0]
    # cwd=HERE and every path anchored to __file__. This file used to read
    # `../reference/...` relative to wherever the gate was started, and
    # `run_cases.py` had the same shape once and printed "0 failure(s)" over
    # 226 cases it had never opened, four of them failing.
    return probe_command(
        [sys.executable, RUNNER, module, *profile_args], cwd=HERE, timeout=PROBE_TIMEOUT
    )


def duplicate_mutations(source=IMPL, mutants=MUTANTS):
    """Pairs of mutants whose mutated source is identical.

    Two names for one mutation count it twice, and a CONTROL that is a copy of
    a mutant cannot fail independently of it (#48). Compared on what the kit
    actually produces, not on the `(old, new)` strings: patterns match a
    normalised token stream, so `rows.append( _ANY )` and `rows.append(_ANY)`
    are one mutation spelled two ways. A mutant that no longer applies is left
    to the gate, which reports it as stale.
    """
    with open(source, encoding="utf-8") as fh:
        src = fh.read()
    seen, dups = {}, []
    for name, spec in mutants.items():
        try:
            out = apply_mutant(src, *spec)
        except MutantError:
            continue
        first = seen.setdefault(hashlib.sha256(out.encode()).hexdigest(), name)
        if first != name:
            dups.append((first, name))
    return dups


def main(argv=()):
    """`mutants.py [--profile mdtbl|csv]`, the profile defaulting to mdtbl.

    Three exit codes, the same three the runner uses and for the same reason.

    A gate that could not run is not a gate that found nothing: an orphaned
    equivalence claim, a scratch path pointing at the implementation, or a
    suite that reaches no verdict on the UNMUTATED source all mean every
    number this run could print would be meaningless.
    """
    with open(LOCK, "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(
                f"waiting for another mutation gate run in this tree to finish ({LOCK})",
                file=sys.stderr,
                flush=True,
            )
            fcntl.flock(lock, fcntl.LOCK_EX)
        return _run(argv)


def _profile(argv):
    """The `--profile` named in `argv`, refused unless it is exactly one known
    name: which implementation the gate measured must never be a guess."""
    args = list(argv)
    if not args:
        return "mdtbl"
    if len(args) == 2 and args[0] == "--profile" and args[1] in TARGETS:
        return args[1]
    raise GateError(f"usage: mutants.py [--profile {'|'.join(TARGETS)}]; got {args}")


def _run(argv=()):
    try:
        source, mutants, equivalent, scratch, profile_args = TARGETS[_profile(argv)]
        for leftover in sorted({t[3] for t in TARGETS.values()}):
            if os.path.lexists(leftover):
                # Possibly a mutant, and gitignored, so nothing else shows it.
                # Writing over it would also erase the evidence that a run died.
                raise GateError(
                    f"{leftover} is left over from a gate run that was interrupted or killed, "
                    "and may hold a mutant: inspect it, delete it, and run the gate again"
                )
        dups = duplicate_mutations(source, mutants)
        if dups:
            raise GateError(f"mutants produce the same mutated source: {dups}")
        report = gate(
            source=source,
            mutants=from_table(mutants, equivalent),
            probe=lambda path: probe(path, profile_args),
            scratch=scratch,
        )
    except GateError as exc:
        print(f"\nHARD FAILURE: {exc}", file=sys.stderr)
        return EXIT_NO_VERDICT
    return EXIT_OK if report.ok else EXIT_FAILURES


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
