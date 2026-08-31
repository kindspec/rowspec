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
and so is an `EQUIVALENT` claim the suite turns out to refute.
"""

import ast
import io
import os
import re
import subprocess
import sys
import textwrap
import tokenize

# Mutations proven to have no observable effect: an earlier fix made the
# mutated line unreachable. A gate cannot distinguish these from suite holes on
# its own, so they are recorded explicitly rather than silently deleted.
#
# These are still APPLIED and still run. An equivalent mutant whose pattern has
# gone stale is just as blind as any other, and an "equivalent" mutant that the
# suite kills is a FALSE equivalence claim -- both are reported as failures.
EQUIVALENT = {
    "float-accepts-thousands-separators": (
        "ev() raises KeyError for any string cell matching [,\\u00a0\\u202f] before "
        "float() is reached, so no string carrying a separator ever gets there; "
        "the only other value that reaches it is a float from an already-computed "
        "column, and str(float) never contains a comma. .replace(',', '') is "
        "therefore a no-op on every reachable input"
    ),
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
ALL = "all-occurrences"

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
        # Spans the initialiser so the mutant can carry the prefix. Rounding
        # `acc + v` once is NOT the alternative reading -- that is precisely
        # what a binary64 addition already does, which made the first attempt
        # at this mutant equivalent. The reading §7 rejects is an exact sum
        # over the whole prefix, rounded once at the end.
        "acc, prev = 0.0, None\n"
        "for r in seq:\n"
        "    try:\n"
        "        v = num(r[src])\n"
        "    except (ValueError, TypeError, KeyError):\n"
        '        r[nm] = f"#REF!({src})"\n'
        "        continue\n"
        '    if fn == "cumulative":\n'
        "        acc += v",
        "acc, prev, _seen = 0.0, None, []\n"
        "for r in seq:\n"
        "    try:\n"
        "        v = num(r[src])\n"
        "    except (ValueError, TypeError, KeyError):\n"
        '        r[nm] = f"#REF!({src})"\n'
        "        continue\n"
        '    if fn == "cumulative":\n'
        "        _seen.append(v)\n"
        "        acc = _exact(_seen, 1)",
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
        'if fn == "cumulative":\n    acc += v\n'
        '    r[nm] = "#REF!(overflow)" if acc in (INF, -INF) else acc',
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
        'elif fn == "prior":\n    r[nm] = prev if prev is not None else ""',
        'elif fn == "prior":\n    r[nm] = ""',
    ),
    "delta-first-row-is-the-value": (
        'elif fn == "delta":\n    d = (v - prev) if prev is not None else ""',
        'elif fn == "delta":\n    r[nm] = v',
    ),
    "delta-is-negated": (
        'elif fn == "delta":\n    d = (v - prev) if prev is not None else ""',
        'elif fn == "delta":\n    r[nm] = (prev - v) if prev is not None else ""',
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
# Matching. A mutant must survive `ruff format`; it must NEVER land on the
# wrong line.
# ---------------------------------------------------------------------------

_SKIP = {
    tokenize.COMMENT,
    tokenize.NL,
    tokenize.NEWLINE,
    tokenize.INDENT,
    tokenize.DEDENT,
    tokenize.ENDMARKER,
    getattr(tokenize, "ENCODING", -1),
}
_WILD = re.compile(r"_ANY\d*")
_FSTART = getattr(tokenize, "FSTRING_START", -2)
_FEND = getattr(tokenize, "FSTRING_END", -3)


class MutantError(Exception):
    """The pattern does not identify exactly one construct in the source."""


def _key(tok):
    """Canonical (type, text) for one token, with quote style erased.

    `ruff format` rewrites 'x' to "x" and rewraps lines. Neither changes the
    token stream once strings are compared by VALUE and layout tokens are
    dropped, so a mutant written against pre-format source still applies.
    """
    t, s = tok.type, tok.string
    if t == tokenize.STRING:
        try:
            return (t, repr(ast.literal_eval(s)))
        except Exception:
            return (t, s)
    if t == _FSTART:  # f' / f" / rf''' ... -> one canonical opener
        return (t, s.rstrip("\"'"))
    if t == _FEND:
        return (t, "")
    return (t, s)


_OPEN, _CLOSE = "([{", ")]}"


def _drop_magic_commas(toks):
    """Delete inert trailing commas: `f(a, b,)` -> `f(a, b)`.

    When a call outgrows the line limit `ruff format` explodes it one argument
    per line AND adds a magic trailing comma. That is a pure layout change, so
    the token stream must not see it. Never dropped where it would turn a
    one-tuple into a parenthesised scalar: `("x",)` keeps its comma.
    """
    kill, stack = set(), []
    for i, t in enumerate(toks):
        if t.type == tokenize.OP and t.string in _OPEN:
            stack.append([t.string, _is_call(toks, i), 0])
        elif t.type == tokenize.OP and t.string in _CLOSE:
            if stack:
                brk, call, commas = stack.pop()
                prev = toks[i - 1]
                if prev.type == tokenize.OP and prev.string == ",":
                    if brk != "(" or call or commas > 1:
                        kill.add(i - 1)
        elif t.type == tokenize.OP and t.string == "," and stack:
            stack[-1][2] += 1
    return [t for i, t in enumerate(toks) if i not in kill]


_KEYWORDS = {
    "lambda",
    "in",
    "not",
    "and",
    "or",
    "if",
    "else",
    "return",
    "yield",
    "assert",
    "while",
    "elif",
    "await",
    "from",
    "import",
    "raise",
    "for",
}


def _is_call(toks, i):
    """Is toks[i] an opening bracket that follows a callable/subscriptable?"""
    if not i:
        return False
    prev = toks[i - 1]
    if prev.type == tokenize.OP:
        return prev.string in _CLOSE
    return (
        prev.type in (tokenize.NAME, tokenize.STRING, tokenize.NUMBER)
        and prev.string not in _KEYWORDS
    )


def _pairs(toks):
    stack, out = [], {}
    for i, t in enumerate(toks):
        if t.type == tokenize.OP and t.string in _OPEN:
            stack.append(i)
        elif t.type == tokenize.OP and t.string in _CLOSE and stack:
            out[stack.pop()] = i
    return out


def _drop_clause_parens(toks, ends_line):
    """Delete parentheses that merely wrap a whole clause.

    `ruff format` parenthesises a condition or a right-hand side that outgrows
    the line limit:  `if a and b:` becomes `if (\n    a\n    and b\n):`. The
    parens are layout, not syntax, so the token stream must not see them.

    Restricted to a pair that runs to the END of its clause -- the `)` closes
    the logical line, or is followed by a `:` that does. Parens in that
    position are always redundant, so erasing them cannot make two
    semantically different constructs compare equal. `(a) * b` is left alone
    (the `)` does not end the clause) and `("x",)` is left alone (a one-tuple
    keeps its comma, so the pair is not empty of top-level commas).
    """
    pairs, kill = _pairs(toks), set()
    for i, j in pairs.items():
        if toks[i].string != "(" or _is_call(toks, i):
            continue
        depth = 0
        for k in range(i + 1, j):
            if toks[k].type == tokenize.OP and toks[k].string in _OPEN:
                depth += 1
            elif toks[k].type == tokenize.OP and toks[k].string in _CLOSE:
                depth -= 1
            elif depth == 0 and toks[k].type == tokenize.OP and toks[k].string == ",":
                break  # a tuple: the parens are load-bearing
        else:
            if (
                j + 1 == len(toks)
                or ends_line[j]
                or (toks[j + 1].string == ":" and ends_line[j + 1])
            ):
                kill |= {i, j}
    return [t for k, t in enumerate(toks) if k not in kill]


def _tokens(src):
    """Significant tokens of a source FRAGMENT, normalised for layout.

    Fragments need not be complete: an unclosed bracket raises TokenError at
    EOF, but every token produced before that point is already yielded.
    """
    raw = []
    try:
        raw = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        raw = _partial(src)
    out, ends = [], []
    for tok in raw:
        if tok.type in _SKIP:
            if tok.type == tokenize.NEWLINE and ends:
                ends[-1] = True
            continue
        out.append(tok)
        ends.append(False)
    keep = _drop_magic_commas(out)
    ends = dict(zip(map(id, out), ends, strict=True))
    return _drop_clause_parens(keep, [ends[id(t)] for t in keep])


def _partial(src):
    """Tokens of a fragment that does not tokenise cleanly (unclosed bracket)."""
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            out.append(tok)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return out


def _offsets(src):
    off, n = [0], 0
    for line in src.splitlines(keepends=True):
        n += len(line)
        off.append(n)
    return off


def _match_at(win, pat):
    """Match one window, binding _ANY wildcards consistently. -> binds | None"""
    binds = {}
    for a, b in zip(win, pat, strict=True):
        ka, kb = _key(a), _key(b)
        if kb[0] == tokenize.NAME and _WILD.fullmatch(kb[1]):
            if ka[0] != tokenize.NAME or binds.setdefault(kb[1], ka[1]) != ka[1]:
                return None
            continue
        if ka != kb:
            return None
    return binds


def apply_mutant(src, old, new, mode=None):
    """Patch `src` by matching `old` as a normalised token sequence.

    Three properties, in priority order:

    * PRECISE -- the pattern must match EXACTLY ONE token run (or, with
      mode=ALL, at least one and every run is patched). An ambiguous pattern
      raises rather than silently patching the first hit; a mutant that lands
      on the wrong line is worse than one that does not apply at all.
    * DURABLE -- comparison is over tokens with string values normalised, so
      quote style, indentation, line wrapping and blank lines are all
      irrelevant. `_ANY`/`_ANY2` in a pattern match any single identifier and
      are substituted back into the replacement, so a mutant anchored on a
      distinctive identifier survives the rename of an incidental one.
    * CHECKED -- the result must parse, and must differ from the input.
    """
    src_toks, pat = _tokens(src), _tokens(textwrap.dedent(old))
    if not pat:
        raise MutantError("empty pattern")
    hits = []
    for i in range(len(src_toks) - len(pat) + 1):
        binds = _match_at(src_toks[i : i + len(pat)], pat)
        if binds is not None:
            hits.append((i, binds))
    if not hits:
        raise MutantError("pattern no longer matches the source")
    if len(hits) > 1 and mode != ALL:
        rows = ", ".join(str(src_toks[i].start[0]) for i, _ in hits)
        raise MutantError(f"pattern is AMBIGUOUS: matches lines {rows}")
    off = _offsets(src)
    out = src
    for i, binds in reversed(hits):  # back to front: earlier spans stay valid
        a = off[src_toks[i].start[0] - 1] + src_toks[i].start[1]
        b = off[src_toks[i + len(pat) - 1].end[0] - 1] + src_toks[i + len(pat) - 1].end[1]
        text = textwrap.dedent(new)
        for w, name in binds.items():
            text = re.sub(rf"\b{w}\b", name, text)
        lines = text.splitlines() or [""]
        if len(lines) > 1:
            bol = out.rfind("\n", 0, a) + 1
            if out[bol:a].strip():
                raise MutantError("multi-line replacement must start a line")
            pad = out[bol:a]
            text = lines[0] + "".join("\n" + pad + ln if ln else "\n" for ln in lines[1:])
        out = out[:a] + text + out[b:]
    if out == src:
        raise MutantError("replacement is a no-op")
    try:
        compile(out, "<mutant>", "exec")
    except SyntaxError as e:
        raise MutantError(f"mutated source does not parse: {e}") from None
    return out


# ---------------------------------------------------------------------------


CRASH = "<runner crashed>"


def failing_cases(impl):
    """Case ids the fixture tree reports as failing for `impl`.

    A SET, not a count. The reference itself does not pass every case -- the
    suite is written adversarially and runs ahead of the implementation -- so
    "the mutant made N cases fail" proves nothing. A mutant is killed only if
    it breaks a case that passes WITHOUT it.
    """
    r = subprocess.run([sys.executable, "run_cases.py", impl], capture_output=True, text=True)
    ids, total = set(), False
    for line in r.stdout.splitlines():
        m = re.match(r"\s+FAIL (\S+)", line)
        if m:
            ids.add(m.group(1))
        elif "failure(s) across the fixture tree" in line:
            total = True
    if not total:
        ids.add(CRASH)  # the runner died on this implementation: that counts
    return ids


def mutant_failures(mutated):
    with open("mutant_impl.py", "w") as fh:
        fh.write(mutated)
    return failing_cases("mutant_impl")


def main():
    src = open("../reference/rowspec/table.py").read()
    base = failing_cases("rowspec.table")
    if base:
        print(f"  BASELINE the reference already fails {len(base)} case(s):")
        for c in sorted(base):
            print(f"    baseline-fail: {c}")
        print("  Kills are counted as cases that fail ONLY under the mutant.\n")
    survived, killed, stale, equiv, bogus = [], [], [], [], []
    for name, spec in MUTANTS.items():
        old, new, mode = (spec + (None,))[:3]
        try:
            mutated = apply_mutant(src, old, new, mode)
        except MutantError as e:
            stale.append((name, str(e)))
            print(f"  STALE   {name:32} {e}")
            continue
        caught = sorted(mutant_failures(mutated) - base)
        if name in EQUIVALENT:
            if caught:
                bogus.append((name, caught))
                print(f"  BOGUS   {name:32} claimed EQUIVALENT but {caught} detects it")
            else:
                equiv.append(name)
                print(f"  equiv   {name:32} ({EQUIVALENT[name]})")
        elif caught:
            killed.append(name)
            print(f"  killed  {name:32} ({len(caught)} case(s): {', '.join(caught[:3])})")
        else:
            survived.append(name)
            print(f"  SURVIVED {name:31} <-- HOLE IN THE SUITE")
    if os.path.exists("mutant_impl.py"):
        os.remove("mutant_impl.py")
    print(
        f"\n{len(killed)} killed, {len(survived)} survived, "
        f"{len(equiv)} equivalent, {len(stale)} stale"
    )
    if stale:
        print("\n  A STALE MUTANT MEASURES NOTHING. The source was reformatted or")
        print("  refactored and these patterns no longer apply, so the gate went")
        print("  quiet without failing -- the exact silent degradation this")
        print("  project exists to eliminate. Update them:")
        for name, why in stale:
            print(f"    stale: {name}: {why}")
    for name, caught in bogus:
        print(f"  FALSE EQUIVALENCE: {', '.join(caught)} detects {name!r}; it is a real mutant")
    for name in survived:
        print(f'  hole: nothing in the suite detects "{name}"')
    return 1 if (survived or stale or bogus) else 0


if __name__ == "__main__":
    sys.exit(main())
