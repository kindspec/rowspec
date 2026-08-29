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
    "computed-columns-evaluated-in-reverse-header-order": (
        "the plain-formula loop is a bounded FIXPOINT: a formula whose "
        "dependency is still pending is skipped and retried next round, and "
        "the round bound len(plain)+1 is sufficient in either direction, so "
        "iteration order over `pending` cannot change the fixed point"
    ),
}

# (old, new) -- or (old, new, ALL) to patch every occurrence rather than
# requiring the pattern to be unique.
ALL = "all-occurrences"

MUTANTS = {
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
        'if fn == "cumulative":\n    acc += v\n    r[nm] = acc',
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
        'elif fn == "delta":\n    r[nm] = (v - prev) if prev is not None else ""',
        'elif fn == "delta":\n    r[nm] = v',
    ),
    "delta-is-negated": (
        'elif fn == "delta":\n    r[nm] = (v - prev) if prev is not None else ""',
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
        'if fn == "sum":\n    return sum(nums)',
        'if fn == "sum":\n    return sum(float(v) for v in vals)',
    ),
    # --- I3's headline promise: a blank cell is NEVER zero ----------------------
    "blank-cell-in-a-real-column-is-zero": (
        'v = env.get(node.id, "")',
        'v = env.get(node.id, "")\nif node.id in env and v == "":\n    return 0.0',
    ),
    # --- numeric coercion, entirely unspecified and entirely untested -----------
    "float-accepts-thousands-separators": (
        "return float(v)",
        'return float(str(v).replace(",", ""))',
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
        "for nm, expr in list(pending.items()):",
        "for nm, expr in reversed(list(pending.items())):",
    ),
    # --- namespaces the suite tests for `key` but not for `order` ---------------
    "allow-duplicate-order-declaration": ("if order_seen:", "if False:"),
    "order-accepts-any-function": (
        'if fn != "by":',
        "if False:",
    ),
    # --- a data row that looks like an alignment row is silently dropped --------
    "is-align-matches-any-dashed-cell": (
        'return bool(cells) and all(_ANY.fullmatch(c) for c in cells if c != "")',
        'return bool(cells) and any(_ANY.fullmatch(c) for c in cells if c != "")',
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
        'return "| " + " | ".join(cells) + " |"',
        'return "| " + " | ".join(c.ljust(12) for c in cells) + " |"',
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
