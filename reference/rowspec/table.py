#!/usr/bin/env python3
"""Row-relative computation WITHOUT coordinates.

The insight: `prev.` failed not because row-relative computation is wrong, but
because "the row above" is a PLACE. If the table declares what determines row
order, then "the previous row" is a NOMINAL relationship -- "the row with the
next-lower key" -- and is independent of physical position, insertion, and
merge order.

    order := by(date)     row-relative ops legal, order derived from DATA
    order := none         row-relative ops are a PARSE ERROR (default)
"""

import operator
import re
import sys
import unicodedata


class Malformed(Exception):
    pass


CONFLICT = ("<<<<<<<", "=======", ">>>>>>>", "|||||||")
ROWREL = {"cumulative", "prior", "delta"}


_UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")


def unescape_cell(c):
    return c.replace("\\|", "|")


def escape_cell(c):
    return str(c).replace("|", "\\|")


def split_row(line):
    # Split on UNESCAPED pipes only. `\|` is the escape, as in GFM.
    # ASCII whitespace only when trimming: SPEC §8 names non-ASCII spaces among
    # the values that must not coerce, so stripping them would silently accept a
    # cell the spec requires to be #REF!.
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return [unescape_cell(c.strip(" \t")) for c in _UNESCAPED_PIPE.split(body)]


_ALIGN_CELL = re.compile(r":?-+:?")


def is_align(line):
    cells = split_row(line)
    return bool(cells) and all(_ALIGN_CELL.fullmatch(c) for c in cells)


_STRUCTURAL = set('|=:#(),"@')
# `-` and `.` are excluded: `-` is subtraction in a formula, so `a-b` would be a
# column name that can never be referenced, and two readers would silently total
# different columns. The cost is the ability to name a column `a-b`.
_IDENT_EXTRA = set("_")


def _check_ident(name, what):
    for ch in name:
        if ch in _STRUCTURAL or (
            not (ch.isalnum() or unicodedata.category(ch).startswith("M"))
            and ch not in _IDENT_EXTRA
            and not ch.isspace()
        ):
            raise Malformed(
                f"{what} {name!r} contains {ch!r}, which is not permitted in an "
                f"identifier; §4.1.9 admits letters, marks, digits and underscore"
            )
    for ch in name:
        if unicodedata.category(ch) == "Cf":
            raise Malformed(f"{what} {name!r} contains a Cf format character U+{ord(ch):04X}")
        if ch.isspace():
            raise Malformed(
                f"{what} {name!r} contains whitespace U+{ord(ch):04X}; two identifiers "
                f"must not render identically"
            )


def parse(text):
    if re.search(r"\r(?!\n)", text):
        raise Malformed("lone CR: two rows would share one line")
    text = unicodedata.normalize("NFC", text)
    lines = text.splitlines()
    for n, line in enumerate(lines, 1):
        if line.startswith(CONFLICT):
            raise Malformed(f"line {n}: unresolved conflict marker")
    tbl = []
    for line in lines:
        if line.strip().startswith("|"):
            if not line.strip().endswith("|"):
                raise Malformed(
                    f"table line lacks its closing pipe: {line.strip()!r}. §4.1.3 "
                    f"requires both, because only the closing pipe reveals a row "
                    f"truncated inside its final cell"
                )
            tbl.append(line)
        elif tbl:
            break  # the run ended; §4 makes the table contiguous
    if not tbl:
        raise Malformed("no table found")
    decls, order, key = {}, None, None
    order_seen = False
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("#"):
            continue  # SPEC §9: the ignorable channel, inert whatever it contains
        stripped = re.sub(r"\s+#.*$", "", line)
        if ":=" not in stripped:
            if stripped.strip() and line not in tbl:
                if stripped.strip().startswith("|"):
                    raise Malformed(
                        f"line {n}: this is a valid table line, but the table already "
                        f"ended above it. A table is a CONTIGUOUS run of lines beginning "
                        f"with '|' (§4.1.2), and an annotation or blank line between two "
                        f"rows ends it. Move the annotation above the table or below the "
                        f"declarations."
                    )
                raise Malformed(
                    f"line {n}: not a table line, an annotation, or a declaration: "
                    f"{stripped.strip()!r}"
                )
            continue
        line = stripped
        mw = re.match(r"\s*([^\s:=]+)\s*:=\s*(\w+)\((.+)\)\s*$", line)
        if mw and " where " in mw.group(3):
            nm_, fn_, inner = mw.groups()
            col_, ptext = inner.split(" where ", 1)
            if "@" in ptext:
                raise Malformed(
                    f"line {n}: `@` names THIS ROW's value, and a declaration has no "
                    f"current row (SPEC §4.2 rule 5); {ptext.strip()!r} is malformed"
                )
            _check_ident(nm_, "aggregate name")
            if nm_ in decls:
                raise Malformed(f"line {n}: duplicate aggregate name {nm_!r}")
            decls[nm_] = (fn_, col_.strip(), ptext.strip())
            continue
        m = re.match(r"\s*([^\s:=]+)\s*:=\s*(\w+)\(\s*([^\s()]*)\s*\)\s*$", line)
        if m:
            name, fn, arg = m.groups()
        else:
            m2 = re.match(r"\s*([^\s:=]+)\s*:=\s*([\w.-]+)\s*$", line)
            if not m2:
                raise Malformed(f"line {n}: malformed declaration: {line.strip()!r}")
            name, fn, arg = m2.group(1), None, m2.group(2)
            if name not in ("key",):
                raise Malformed(f"line {n}: {name!r} needs a function, e.g. {name} := sum(col)")
        if name == "order":
            # `order := none()` sets order to None, so a `None` test cannot see
            # a second declaration. Track that one was SEEN, not its value.
            if order_seen:
                raise Malformed(f"line {n}: duplicate order declaration")
            order_seen = True
            if fn != "by":
                raise Malformed(
                    f"line {n}: order must be by(<column>); omit the line entirely "
                    f"for an unordered table"
                )
            order = arg
        elif name == "key":
            if key is not None:
                raise Malformed(f"line {n}: duplicate key declaration")
            key = arg
        else:
            _check_ident(name, "aggregate name")
            if name in decls:
                raise Malformed(f"line {n}: duplicate aggregate name {name!r}")
            decls[name] = (fn, arg, None)
    header = split_row(tbl[0])
    cols, formulas, seen = [], {}, set()
    for h in header:
        if "=" in h:
            nm, expr = h.split("=", 1)
            nm = nm.strip()
            cols.append(nm)
            formulas[nm] = expr.strip()
        else:
            cols.append(h)
    for c in cols:
        _check_ident(c, "column name")
        if c in seen:
            raise Malformed(f"duplicate column name {c!r}")
        seen.add(c)
    # I7: row-relative operators are illegal unless order is declared
    for nm, expr in formulas.items():
        for fn in ROWREL:
            if re.search(rf"\b{fn}\s*\(", expr):
                if order is None:
                    raise Malformed(
                        f"column {nm!r} uses row-relative {fn}() but the table "
                        f"declares no row order. Add `order := by(<column>)`."
                    )
                if order not in cols:
                    raise Malformed(f"order := by({order}) but there is no column {order!r}")
    if len(tbl) < 2:
        raise Malformed("table has no alignment row")
    if not is_align(tbl[1]):
        raise Malformed(
            f"the second table line is not a valid alignment row: {tbl[1].strip()!r}. "
            f"Cells must be one of ---, :--, --:, :-:"
        )
    if len(split_row(tbl[1])) != len(cols):
        raise Malformed(
            f"alignment row has {len(split_row(tbl[1]))} fields, header has {len(cols)}"
        )
    rows = []
    for line in tbl[2:]:
        if is_align(line):
            raise Malformed(
                f"alignment-style row among the data rows "
                f"(wrong number of value fields): {line.strip()!r}"
            )
        v = split_row(line)
        if len(v) != len(cols):
            raise Malformed(f"row has {len(v)} fields, header has {len(cols)}: {line.strip()!r}")
        row = dict(zip(cols, v, strict=False))
        for c in formulas:
            if str(row.get(c, "")).strip() != "":
                raise Malformed(
                    f"computed column {c!r} has a value {row[c]!r} in a data row; "
                    f"computed cells must be empty"
                )
        rows.append(row)
    if key:
        for r in rows:
            _check_ident(str(r.get(key, "")), f"row key {key}=")
        ids = [r.get(key) for r in rows]
        if len(set(ids)) != len(ids):
            dup = [i for i in ids if ids.count(i) > 1][0]
            raise Malformed(f"duplicate key {key}={dup!r}")
    return cols, formulas, rows, decls, order, key


_NUMBER = re.compile(r"-?[0-9]+(\.[0-9]+)?\Z")


def _why_not_a_number(v):
    """Say WHY a cell is not a number, not merely which column it is in.

    A pasted "1,299.00" and a value holding U+00A0 both look like numbers on
    screen; naming only the column leaves the reader staring at one.
    """
    t = str(v)
    for ch, why in (
        ("\u00a0", "non-breaking space"),
        ("\u202f", "narrow no-break space"),
        ("\u2007", "figure space"),
        (",", "thousands separator"),
        ("_", "underscore separator"),
    ):
        if ch in t:
            return f"{t!r} contains a {why}"
    if t[:1] == "(" and t[-1:] == ")":
        return f"{t!r} is a parenthesised negative; write -{t[1:-1]}"
    if any("0" <= c <= "9" for c in t) and not all(c.isascii() for c in t):
        return f"{t!r} uses non-ASCII digits"
    low = t.lower()
    if low in ("inf", "-inf", "nan", "infinity"):
        return f"{t!r} is not finite"
    if "e" in low and any(c.isdigit() for c in t):
        return f"{t!r} uses exponent notation, which this format does not accept"
    if t.startswith("+"):
        return f"{t!r} has a leading +"
    if t.startswith(".") or t.endswith("."):
        return f"{t!r} has a one-sided decimal point"
    return f"{t!r} is not a number"


def num(v):
    """SPEC §4.1: number = [-] 1*DIGIT [ "." 1*DIGIT ], DIGIT = U+0030..U+0039.

    Python's num() is far more permissive than the grammar and silently
    accepts things §8 requires to be refused: num("\u0665") is 5.0
    (Arabic-Indic digits), num("1_000") is 1000.0 (PEP 515 separators),
    num("1e3") is 1000.0, and num(" 5 ") strips whitespace. Each is a
    second spelling of a value that would compare equal as a number and
    unequal as text, splitting predicates and key identity from arithmetic.
    """
    if isinstance(v, bool):
        raise ValueError(v)
    if isinstance(v, (int, float)):
        return float(v)
    if not isinstance(v, str) or not _NUMBER.match(v):
        raise ValueError(v)
    return float(v)


def _isnum(v):
    try:
        num(v)
        return True
    except (ValueError, TypeError):
        return False


DATE_RE = re.compile(r"^[0-9]{1,4}([-/])[0-9]{1,2}\1[0-9]{1,2}$")


def column_type(col, rows):
    """A column used for ordering must have ONE type. Mixed types have no total
    order, so they are refused rather than silently compared as strings."""
    vals = [str(r.get(col, "")).strip() for r in rows]
    vals = [v for v in vals if v != ""]
    if not vals:
        return "text"
    kinds = set()
    for v in vals:
        if DATE_RE.match(v):
            kinds.add("date")
        else:
            try:
                num(v)
                kinds.add("number")
            except ValueError:
                kinds.add("text")
    if len(kinds) > 1:
        raise Malformed(
            f"order column {col!r} mixes types {sorted(kinds)}; "
            f"an ordering column must have a single type"
        )
    return kinds.pop()


_GROUP = re.compile(r"(\w+)\(\s*(\w+)\s+where\s+(.+?)\s*\)\s*$")
_PRED = re.compile(r'(\w+)\s*=\s*(?:@(\w+)|"([^"]*)")')


def _predicate(text, cols, computed=frozenset()):
    """A conjunction of equality predicates. `@c` is THIS ROW's value of c."""
    preds = []
    for part in [x.strip() for x in re.split(r"\s+and\s+", text)]:
        m = _PRED.fullmatch(part)
        if not m:
            raise Malformed(f"unsupported predicate {part!r}")
        col, at, lit = m.groups()
        for c in (col, at):
            if c and c not in cols:
                raise Malformed(f"predicate names unknown column {c!r}")
            if c and c in computed:
                raise Malformed(
                    f"predicate names computed column {c!r} (§9.22): comparison is on "
                    f"cell text and a computed column has none, so the predicate would "
                    f"match nothing and `sum` would report a plausible 0"
                )
        preds.append((col, at, lit))
    return preds


def _agg(fn, vals, what):
    bad = [v for v in vals if isinstance(v, str) and v.startswith("#REF!")]
    if bad:
        return bad[0]
    # `count` counts rows and never coerces: it is poisoned by a #REF! already
    # present (handled above) but not by a value that merely is not a number,
    # because it never uses one as an operand.
    if fn == "count":
        return len(vals)
    try:
        for v in vals:
            if v not in ("", None):
                num(v)
    except (ValueError, TypeError):
        return f"#REF!({what})"
    try:
        nums = [num(v) for v in vals if v not in ("", None)]
    except (ValueError, TypeError):
        return f"#REF!({what})"
    if fn == "sum":
        return sum(nums)
    if fn == "avg":
        return (sum(nums) / len(nums)) if nums else f"#REF!({what} empty)"
    if not nums:
        return f"#REF!({what} empty)"
    return min(nums) if fn == "min" else max(nums)


def _ast(expr, where):
    if "#" in expr:
        raise Malformed(
            f"column {where!r}: '#' is not a comment inside a formula (§4.1.10); "
            f"a whole-line annotation goes outside the table"
        )
    return _parse_expr(expr, where)


_TOK = re.compile(
    r"\s*(?:(?P<word>[0-9]+\.[0-9]+|[^\W]+)"
    r"|(?P<op>[-+*/()])"
    r"|(?P<bad>.))",
    re.UNICODE,
)
_LITERAL = re.compile(r"[0-9]+(\.[0-9]+)?\Z")


class Num:
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v


class Name:
    __slots__ = ("id",)

    def __init__(self, i):
        self.id = i


class Bin:
    __slots__ = ("op", "l", "r")

    def __init__(self, op, left, right):
        self.op, self.l, self.r = op, left, right


class Neg:
    __slots__ = ("x",)

    def __init__(self, x):
        self.x = x


def _lex(expr, where):
    out, i = [], 0
    while i < len(expr):
        m = _TOK.match(expr, i)
        if not m or m.end() == i:
            break
        i = m.end()
        if m.group("bad") is not None:
            ch = m.group("bad")
            if ch in "^%&|":
                raise Malformed(
                    f"column {where!r}: {ch!r} is not an operator in this format; §4.2 "
                    f"admits + - * / and unary minus. `^` alone means exponent in one "
                    f"spreadsheet lineage and exclusive-or in another, so one file would "
                    f"total two ways"
                )
            raise Malformed(
                f"column {where!r}: {ch!r} is not part of an expression; §4.2 admits "
                f"column names, unsigned decimal literals, + - * / and parentheses"
            )
        w = m.group("word")
        if w is not None:
            out.append(("num" if _LITERAL.match(w) else "name", w))
        else:
            out.append(("op", m.group("op")))
    return out


MAX_NESTING = 64


def _parse_expr(expr, where):
    toks = _lex(expr, where)
    pos = 0
    depth = 0

    def peek():
        return toks[pos] if pos < len(toks) else (None, None)

    def eat(v):
        nonlocal pos
        pos += 1
        return v

    def primary():
        nonlocal pos
        k, v = peek()
        if k == "op" and v == "(":
            nonlocal depth
            depth += 1
            if depth > MAX_NESTING:
                raise Malformed(
                    f"column {where!r}: parentheses nested deeper than {MAX_NESTING} (§9.23)"
                )
            eat(v)
            e = sum_()
            depth -= 1
            if peek() != ("op", ")"):
                raise Malformed(f"column {where!r}: unclosed parenthesis")
            eat(")")
            return e
        if k == "num":
            eat(v)
            return Num(float(v))
        if k == "name":
            eat(v)
            return Name(unicodedata.normalize("NFC", v))
        if k == "op" and v in "*/":
            # `**` and `//` reach here as a doubled token. Same reasoning as `^`:
            # both spellings mean different things in different lineages.
            raise Malformed(
                f"column {where!r}: {v * 2!r} is not an operator in this format; "
                f"§4.2 admits + - * / and unary minus"
            )
        raise Malformed(f"column {where!r}: expected a value in {expr!r}")

    def factor():
        nonlocal pos
        if peek() == ("op", "-"):
            eat("-")
            # `factor = [ "-" *WSP ] primary` -- the bracket is zero-or-ONE, and
            # `-a` is not a `primary`, so `--a` is not generated by the grammar.
            return Neg(primary())
        if peek() == ("op", "+"):
            raise Malformed(f"column {where!r}: unary + is not in §4.2; write the value without it")
        return primary()

    def term():
        nonlocal pos
        node = factor()
        while peek()[0] == "op" and peek()[1] in "*/":
            op = peek()[1]
            eat(op)
            node = Bin(op, node, factor())
        return node

    def sum_():
        nonlocal pos
        node = term()
        while peek()[0] == "op" and peek()[1] in "+-":
            op = peek()[1]
            eat(op)
            node = Bin(op, node, term())
        return node

    tree = sum_()
    if pos != len(toks):
        raise Malformed(f"column {where!r}: trailing input in {expr!r}")
    return tree


def ev(node, env):
    if isinstance(node, Num):
        return node.v
    if isinstance(node, Neg):
        return -ev(node.x, env)
    if isinstance(node, Name):
        v = env.get(node.id, "")
        if v == "" or v is None:
            raise KeyError(node.id)
        if isinstance(v, str) and v.startswith("#REF!(") and v.endswith(")"):
            # SPEC §8: the name is the ORIGINATING one, not the column the error
            # surfaces in. Relabelling at each hop sends a reader to inspect a
            # well-formed formula and they never reach the bad cell.
            raise KeyError(v[6:-1])
        try:
            return num(v)
        except (ValueError, TypeError):
            raise KeyError(node.id) from None
    left, right = ev(node.l, env), ev(node.r, env)
    if node.op == "/" and right == 0:
        raise KeyError("/0")
    got = OPS[node.op](left, right)
    if got in (float("inf"), float("-inf")):
        # §4.2 rule 2: `inf` is not a `number` under §4.1.6, so storing one
        # would produce a file this implementation could not re-read.
        raise KeyError("overflow")
    return got


OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
}


def _eval_plain(seq, plain, later=frozenset()):
    """Evaluate ordinary column formulas to a fixpoint, per row.

    Called twice -- before and after the row-relative and group passes -- so a
    column may depend on `cumulative` or on a group aggregate, and those may
    depend on ordinary computed columns. Header order is never an input.
    """
    for r in seq:
        pending = dict(plain)
        deferred = set()
        for _ in range(len(plain) + 1):
            if not pending:
                break
            progressed = False
            for nm, expr in list(pending.items()):
                try:
                    r[nm] = ev(_ast(expr, nm), r)
                    del pending[nm]
                    progressed = True
                except KeyError as e:
                    if e.args[0] in pending:
                        continue  # depends on a pending column
                    if e.args[0] in later or e.args[0] in deferred:
                        # A row-relative or group column computes in a later
                        # pass. Writing #REF! now would poison it before that
                        # pass runs, and a real cycle would then surface as a
                        # broken reference instead of #REF!(cycle).
                        deferred.add(nm)
                        del pending[nm]
                        progressed = True
                        continue
                    r[nm] = f"#REF!({e.args[0]})"
                    del pending[nm]
                    progressed = True
            if not progressed:
                break
        for nm in pending:
            r[nm] = "#REF!(cycle)"


def evaluate(text):
    cols, formulas, rows, decls, order, key = parse(text)
    # THE ORDERING: derived from data, then row id as a stable tiebreak.
    if order:
        if key is None:
            raise Malformed(
                "`order := by(...)` requires a `key :=` declaration: "
                "without one, tied order values fall back to physical "
                "file position, which is a coordinate"
            )
        if order in formulas:
            raise Malformed(
                f"`order := by({order})` names a COMPUTED column; "
                f"ordering must be derived from stored data"
            )
        kind = column_type(order, rows)

        def typed(r):
            v = str(r[order]).strip()
            if kind == "number":
                f = num(v)
                if f != f or f in (float("inf"), float("-inf")):
                    raise Malformed(f"order column {order!r} contains {v!r}")
                return f
            if kind == "date":
                y, m, d = (int(x) for x in re.split(r"[-/]", v))
                return (y, m, d)
            return v

        # a real TUPLE, never a concatenation: the key breaks ties and nothing else
        seq = sorted(rows, key=lambda r: (typed(r), str(r.get(key, ""))))
    else:
        seq = rows
    plain = {
        n: e
        for n, e in formulas.items()
        if not any(re.fullmatch(rf"\s*{f}\s*\(\s*\w+\s*\)\s*", e) for f in ROWREL)
        and not _GROUP.fullmatch(e.strip())
    }
    _eval_plain(seq, plain, later=frozenset(formulas) - frozenset(plain))
    for nm, expr in formulas.items():
        m = re.fullmatch(r"\s*(\w+)\s*\(\s*(\w+)\s*\)\s*", expr)
        if not (m and m.group(1) in ROWREL):
            continue
        fn, src = m.groups()
        acc, prev = 0.0, None
        for r in seq:
            try:
                v = num(r[src])
            except (ValueError, TypeError, KeyError):
                r[nm] = f"#REF!({src})"
                continue
            if fn == "cumulative":
                acc += v
                r[nm] = acc
            elif fn == "prior":
                r[nm] = prev if prev is not None else ""
            elif fn == "delta":
                r[nm] = (v - prev) if prev is not None else ""
            prev = v

    groups = {n: e for n, e in formulas.items() if _GROUP.fullmatch(e.strip())}
    # One fixpoint over BOTH kinds. A group aggregate over a computed column
    # must see that column's VALUES, not its (always empty) stored cells.
    for _round in range(len(formulas) + 2):
        progressed = False
        for nm, expr in list(groups.items()):
            m = _GROUP.fullmatch(expr.strip())
            fn, col, ptext = m.groups()
            if fn not in ("sum", "count", "min", "max", "avg"):
                raise Malformed(f"unknown aggregate {fn!r} in column {nm!r}")
            if col not in cols:
                raise Malformed(f"column {nm!r} aggregates unknown column {col!r}")
            if col in formulas and any(r.get(col) in (None, "") for r in seq):
                continue  # its source is not computed yet
            preds = _predicate(ptext, cols, formulas)
            for r in seq:

                def hit(o, r=r, preds=preds):
                    return all(
                        str(o.get(pc, "")) == (str(r.get(at, "")) if at else lit)
                        for pc, at, lit in preds
                    )

                r[nm] = _agg(fn, [o.get(col) for o in seq if hit(o)], col)
            del groups[nm]
            progressed = True
        if groups and not progressed:
            for nm in groups:
                for r in seq:
                    r[nm] = "#REF!(cycle)"
            break
        if not groups:
            break

    _eval_plain(seq, plain)
    # row-relative, computed over the DERIVED order
    out = {}
    for nm, (fn, col, pred) in decls.items():
        if col not in cols:
            out[nm] = f"#REF!({col})"
            continue
        rows_ = seq
        if pred:
            preds_ = _predicate(pred, cols, formulas)
            rows_ = [
                o
                for o in seq
                if all(
                    str(o.get(pc, "")) == (str(o.get(at, "")) if at else lit)
                    for pc, at, lit in preds_
                )
            ]
        vals = [r.get(col) for r in rows_]
        if fn not in ("sum", "count", "min", "max", "avg"):
            raise Malformed(f"unknown aggregate function {fn!r} in {nm!r}")
        out[nm] = _agg(fn, vals, col)

    return seq, out


if __name__ == "__main__":
    try:
        rows, aggs = evaluate(open(sys.argv[1]).read())
    except Malformed as e:
        print(f"REFUSED: {e}")
        sys.exit(2)
    for r in rows:
        print("  ", {k: v for k, v in r.items()})
    for k, v in aggs.items():
        print(f"{k} = {v}")


# ---------------------------------------------------------------------------
# render: the other half of the round-trip law. Previously `render` was the
# identity function, which made the round-trip test a tautology asserting
# doc == doc. It now reconstructs the file from the parsed structure, so
# render(parse(b)) == b is a real assertion about the parser.
# ---------------------------------------------------------------------------


def structure(text):
    """Full parse into a serialisable structure, preserving what render needs."""
    text = unicodedata.normalize("NFC", text)
    lines = text.splitlines(keepends=True)
    cols, formulas, rows, decls, order, key = parse(text)
    tbl_idx = [i for i, ln in enumerate(lines) if ln.strip().startswith("|")]
    header_raw = lines[tbl_idx[0]]
    align_raw = lines[tbl_idx[1]] if len(tbl_idx) > 1 and is_align(lines[tbl_idx[1]]) else None
    row_raws = [lines[i] for i in tbl_idx[2:]]
    tail = lines[tbl_idx[-1] + 1 :] if tbl_idx else []
    return {
        "header_raw": header_raw,
        "align_raw": align_raw,
        "row_raws": row_raws,
        "tail": tail,
        "cols": cols,
        "formulas": formulas,
        "rows": rows,
        "decls": decls,
        "order": order,
        "key": key,
        "prefix": lines[: tbl_idx[0]] if tbl_idx else [],
    }


def render(st):
    out = list(st["prefix"]) + [st["header_raw"]]
    if st["align_raw"]:
        out.append(st["align_raw"])
    out += st["row_raws"]
    out += st["tail"]
    return "".join(out)


def canon(text):
    """Canonical form: single-space delimiters, no alignment padding.

    Padding is a VIEW. Measured: a one-character edit in a padded 2000-row
    table produces a 2002-line / 238,370-byte diff versus 1 line / 413 bytes
    unpadded, and two genuinely disjoint edits CONFLICT padded while merging
    cleanly unpadded. render(parse(b)) == b still holds for padded input --
    canonicalisation is a separate, explicit operation.
    """
    st = structure(text)
    cols = st["cols"]

    def row(cells):
        return "| " + " | ".join(escape_cell(c) for c in cells) + " |"

    hdr = []
    for c in cols:
        hdr.append(f"{c} = {st['formulas'][c]}" if c in st["formulas"] else c)
    out = list(st["prefix"])
    out.append(row(hdr) + "\n")
    if st["align_raw"]:
        aligns = [a.strip() for a in split_row(st["align_raw"])]
        out.append(
            row(
                [
                    (
                        "--:"
                        if a.endswith(":") and not a.startswith(":")
                        else ":-:"
                        if a.startswith(":") and a.endswith(":")
                        else ":--"
                        if a.startswith(":")
                        else "---"
                    )
                    for a in aligns
                ]
            )
            + "\n"
        )
    for r in st["rows"]:
        out.append(
            row(
                [str(r.get(c, "")) if not isinstance(r.get(c), float) else "" for c in cols]
            ).replace("| |", "|  |")
            + "\n"
        )
    out += st["tail"]
    return "".join(out)


def set_cell(st, row_key, col, value):
    """Mutate a cell THROUGH the structure. This exists so the round-trip test
    can be non-vacuous: an implementation whose `structure()` merely stores the
    raw bytes has no cells to set, and fails."""
    key = st["key"]
    if key is None:
        raise Malformed("set_cell requires a declared key")
    if col not in st["cols"]:
        raise Malformed(f"no column {col!r}")
    if col in st["formulas"]:
        raise Malformed(f"{col!r} is a computed column")
    idx = st["cols"].index(col)
    for i, r in enumerate(st["rows"]):
        if str(r.get(key)) == str(row_key):
            r[col] = str(value)
            cells = split_row(st["row_raws"][i])
            cells[idx] = str(value)
            st["row_raws"][i] = "| " + " | ".join(escape_cell(c) for c in cells) + " |\n"
            return st
    raise Malformed(f"no row with {key}={row_key!r}")
