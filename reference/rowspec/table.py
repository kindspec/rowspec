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
    r"\s*(?:(?P<str>\"[^\"]*\")"
    r"|(?P<word>[0-9]+\.[0-9]+|[^\W]+)"
    r"|(?P<op><=|>=|<>|==|!=|[-+*/(),<>=])"
    r"|(?P<bad>.))",
    re.UNICODE,
)
_LITERAL = re.compile(r"[0-9]+(\.[0-9]+)?\Z")
_ORDER_OP = ("<", "<=", ">", ">=")
_EQ_OP = ("=", "<>")


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


class Cmp:
    """§4.2 rule 10. NOT an expression: a comparison has no value, only a
    truth, and it exists nowhere but as `if`'s first argument. That is what
    keeps the format's values at `number | error` with no boolean."""

    __slots__ = ("op", "lhs", "kind", "rhs")

    def __init__(self, op, lhs, kind, rhs):
        self.op, self.lhs, self.kind, self.rhs = op, lhs, kind, rhs


class If:
    __slots__ = ("c", "a", "b")

    def __init__(self, c, a, b):
        self.c, self.a, self.b = c, a, b


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
        if m.group("str") is not None:
            out.append(("str", m.group("str")[1:-1]))
            continue
        w = m.group("word")
        if w is not None:
            # §4.2 rule 4: a name is a function name ONLY when `(` touches it,
            # with no WSP. The lexer is the only place that can still see the
            # gap, so the distinction is drawn here rather than in the parser.
            if i < len(expr) and expr[i] == "(":
                out.append(("call", w))
            else:
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
        if k == "call":
            return cond()
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

    def want(tok, what):
        if peek() != tok:
            raise Malformed(f"column {where!r}: expected {what} in {expr!r}")
        eat(tok[1])

    def comparison():
        nonlocal pos
        k, v = peek()
        # `comparison = ident ...`. The left side is a NAME position (§4.2
        # rule 7), like the left side of a `where` equality, so a bare `3`
        # there is the column named 3 and never the number.
        if k not in ("name", "num"):
            raise Malformed(
                f"column {where!r}: the left of a comparison in if() must be a "
                f"column name (§4.2 rule 10)"
            )
        eat(v)
        lhs = unicodedata.normalize("NFC", v)
        k2, op = peek()
        if k2 != "op" or op not in _ORDER_OP + _EQ_OP:
            if op in ("==", "!="):
                raise Malformed(
                    f"column {where!r}: {op!r} is not in §4.2; equality is `=` and "
                    f"inequality is `<>`, matching the `where` predicate and every "
                    f"spreadsheet lineage. A second spelling of one comparison is "
                    f"refused for §4.1.6's reason"
                )
            raise Malformed(
                f"column {where!r}: if() takes a comparison first (§4.2 rule 10); "
                f"admitted operators are < <= > >= = <>"
            )
        eat(op)
        # `signed = [ "-" *WSP ] literal`. Without it `if(a > -1, 1, 0)` -- an
        # ordinary guard, and `-1` an ordinary cell value -- is unwritable, and
        # the only workaround is a stored column holding -1.
        sign = 1.0
        if peek() == ("op", "-"):
            eat("-")
            sign = -1.0
        k3, v3 = peek()
        if sign < 0 and k3 != "num":
            raise Malformed(
                f"column {where!r}: only a numeric literal may be negated on the "
                f"right of {op!r} (§4.2 rule 10)"
            )
        if op in _ORDER_OP:
            if k3 == "num":
                kind, rhs = "num", sign * float(v3)
            elif k3 == "name":
                kind, rhs = "name", unicodedata.normalize("NFC", v3)
            elif k3 == "str":
                raise Malformed(
                    f"column {where!r}: {op!r} compares numbers, never text (§4.2 "
                    f"rule 10). Ordering text means collation, and collation is "
                    f"locale-dependent, so two conforming readers would disagree"
                )
            else:
                raise Malformed(f"column {where!r}: expected a value after {op!r}")
        else:
            if k3 == "num":
                kind, rhs = "num", sign * float(v3)
            elif k3 == "str":
                kind, rhs = "str", v3
            elif k3 == "name":
                raise Malformed(
                    f"column {where!r}: a column name on the right of {op!r} is "
                    f"refused (§9.24). The spelling of the right-hand side is what "
                    f"chooses text or numeric comparison, and a column has no "
                    f"spelling to read: `1` and `1.0` compare equal as numbers and "
                    f"unequal as text"
                )
            else:
                raise Malformed(f"column {where!r}: expected a value after {op!r}")
        eat(v3)
        return Cmp(op, lhs, kind, rhs)

    def cond():
        nonlocal pos, depth
        k, name = peek()
        if name != "if":
            raise Malformed(
                f"column {where!r}: unknown function {name!r}; §4.2 admits if() in an "
                f"expression, and cumulative/prior/delta/sum/count/min/max/avg as the "
                f"whole formula"
            )
        eat(name)
        depth += 1
        if depth > MAX_NESTING:
            raise Malformed(f"column {where!r}: nested deeper than {MAX_NESTING} (§9.23)")
        want(("op", "("), "'(' after if")
        c = comparison()
        want(("op", ","), "',' after if's comparison")
        a = sum_()
        want(("op", ","), "',' after if's second argument")
        b = sum_()
        want(("op", ")"), "')' closing if")
        depth -= 1
        return If(c, a, b)

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
        k, v = peek()
        if k == "op" and v in _ORDER_OP + _EQ_OP + ("==", "!="):
            raise Malformed(
                f"column {where!r}: {v!r} is not an operator of an expression "
                f"(§4.2 rule 1). A comparison exists only inside if(), because the "
                f"format has numbers and errors and no boolean for {expr!r} to have"
            )
        raise Malformed(f"column {where!r}: trailing input in {expr!r}")
    return tree


def _cell(name, env):
    """The raw cell text of `name`, with an error value re-raised at its origin.

    Blank is returned as `""` rather than raised, because §4.2 rule 10's
    `if(x = "", ...)` is the one place a blank is data. Every caller that needs
    a NUMBER goes through `_number` instead, which is loud.
    """
    # `env[name]`, never `env.get(name, "")`. The default returns the same
    # sentinel for "this cell is empty" and "there is no such column", in every
    # host language, and that accident made `if(nope = "", a, b)` fire the
    # missing-data fallback in EVERY row -- a mistyped column name turning
    # "use this when that is missing" into "always", with no diagnostic. §8: a
    # reference to a name that does not exist is #REF!(name), under every
    # operator. The KeyError this raises is that #REF!.
    v = env[name]
    if v is None:
        v = ""
    if isinstance(v, str) and v.startswith("#REF!(") and v.endswith(")"):
        raise KeyError(v[6:-1])
    return v


def _number(name, env):
    v = _cell(name, env)
    if v == "":
        raise KeyError(name)
    try:
        return num(v)
    except (ValueError, TypeError):
        raise KeyError(name) from None


def truth(c, env):
    """§4.2 rule 10. Ordering is numeric always; `=`/`<>` take their kind from
    the RIGHT-HAND SIDE'S SPELLING, never from the data -- a grammar that
    cannot be read without the table is not a grammar (rule 7)."""
    if c.op in _EQ_OP:
        if c.kind == "str":
            lv = _cell(c.lhs, env)
            eq = unicodedata.normalize("NFC", str(lv)) == unicodedata.normalize("NFC", c.rhs)
            return eq if c.op == "=" else not eq
        eq = _number(c.lhs, env) == c.rhs
        return eq if c.op == "=" else not eq
    a = _number(c.lhs, env)
    b = c.rhs if c.kind == "num" else _number(c.rhs, env)
    if c.op == "<":
        return a < b
    if c.op == "<=":
        return a <= b
    if c.op == ">":
        return a > b
    return a >= b


def ev(node, env):
    if isinstance(node, Num):
        return node.v
    if isinstance(node, If):
        # ONLY the selected branch. Eager evaluation of both makes
        # `if(qty > 0, total / qty, 0)` -- the guard every spreadsheet lineage
        # writes -- report #REF!(/0) on exactly the rows it was written for.
        return ev(node.a, env) if truth(node.c, env) else ev(node.b, env)
    if isinstance(node, Neg):
        return -ev(node.x, env)
    if isinstance(node, Name):
        # SPEC §8: an error names the ORIGINATING column, not the one it
        # surfaces in -- `_cell` re-raises it that way. Relabelling at each hop
        # sends a reader to inspect a well-formed formula and they never reach
        # the bad cell.
        return _number(node.id, env)
    left, right = ev(node.l, env), ev(node.r, env)
    if node.op == "/" and right == 0:
        raise KeyError("/0")
    got = OPS[node.op](left, right)
    if got in (float("inf"), float("-inf")):
        # §4.2 rule 2: `inf` is not a `number` under §4.1.6, so storing one
        # would produce a file this implementation could not re-read.
        raise KeyError("overflow")
    return got


def str_cmp_lhs(node, out=None):
    """Columns compared against a STRING literal inside an `if` (§9.22).

    A numeric comparison against a computed column is fine -- it has a number.
    A TEXT one is not: §5 requires a computed column's cells empty, so the only
    available reading compares against the rendered form of a number, and §2
    leaves rendering to the implementation. Measured, this implementation says
    `20.0` and refuses to match `"20"`, while one that renders `20` matches --
    a plausible number in every cell and a diagnostic in none.
    """
    if out is None:
        out = set()
    if isinstance(node, Neg):
        str_cmp_lhs(node.x, out)
    elif isinstance(node, Bin):
        str_cmp_lhs(node.l, out)
        str_cmp_lhs(node.r, out)
    elif isinstance(node, If):
        if node.c.kind == "str":
            out.add(node.c.lhs)
        str_cmp_lhs(node.a, out)
        str_cmp_lhs(node.b, out)
    return out


def names_of(node, out=None):
    """Every column this formula MENTIONS, both branches of every `if`.

    §4.2 rule 10: evaluation is lazy but dependency and cycle analysis is
    static. If the untaken branch were excluded, whether a table has a cycle
    would depend on its data, so one inserted row could turn a working table
    cyclic -- and two branches inserting different rows could disagree about
    it, which is the silent-wrong merge the format exists to remove.
    """
    if out is None:
        out = set()
    if isinstance(node, Name):
        out.add(node.id)
    elif isinstance(node, Neg):
        names_of(node.x, out)
    elif isinstance(node, Bin):
        names_of(node.l, out)
        names_of(node.r, out)
    elif isinstance(node, If):
        out.add(node.c.lhs)
        if node.c.kind == "name":
            out.add(node.c.rhs)
        names_of(node.a, out)
        names_of(node.b, out)
    return out


OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
}


def _eval_plain(seq, plain, later=frozenset(), computed=frozenset(), cols=frozenset()):
    """Evaluate ordinary column formulas by DEPENDENCY, per row.

    Called twice -- before and after the row-relative and group passes -- so a
    column may depend on `cumulative` or on a group aggregate, and those may
    depend on ordinary computed columns. Header order is never an input (§4.2
    rule 9).

    Readiness is decided from the STATIC name set, not from whether an
    evaluation happens to raise. With `if` that distinction is load-bearing:
    a lazy branch can compute a value without ever touching a column the
    formula still depends on, and a trial-and-error fixpoint would then commit
    that value before finding out the column was on a cycle.
    """
    # Parsed once per table rather than once per cell per row: the trees are
    # pure, and re-parsing was the evaluator's dominant cost. It also means a
    # malformed formula is refused on a table with no rows, which it must be --
    # §9.20 is about the bytes, and acceptance may not depend on the data.
    trees = {nm: _ast(expr, nm) for nm, expr in plain.items()}
    for nm, t in trees.items():
        for c in sorted(str_cmp_lhs(t) & computed):
            raise Malformed(
                f"column {nm!r}: if() compares computed column {c!r} against a "
                f"string (§9.22). A computed column has no cell text, so the only "
                f"reading left compares against a rendered number and §2 leaves "
                f"rendering to the implementation -- one reader matches {c!r} and "
                f"another does not, and both report a number. Compare it against a "
                f"numeric literal instead"
            )
    deps = {nm: names_of(t) for nm, t in trees.items()}
    # §4.2 rule 10: whether a name RESOLVES is a property of the header, so it
    # is the same answer in every row -- including a row whose `if` selects the
    # other branch. Otherwise a merge that adds the first row taking that branch
    # poisons the column, and every aggregate over it, without touching a
    # formula or a header.
    unresolved = {}
    if cols:
        for nm, d in deps.items():
            miss = sorted(d - set(cols))
            if miss:
                unresolved[nm] = f"#REF!({miss[0]})"
    for r in seq:
        pending = set(plain)
        deferred = set()
        while pending:
            progressed = False
            for nm in sorted(pending):
                d = deps[nm]
                if d & (later | deferred):
                    # A row-relative or group column computes in a later pass.
                    # Writing #REF! now would poison it before that pass runs,
                    # and a real cycle would then surface as a broken reference
                    # instead of #REF!(cycle).
                    deferred.add(nm)
                    pending.discard(nm)
                    progressed = True
                    continue
                if d & pending:
                    continue  # waits on a pending column, itself included
                if nm in unresolved:
                    r[nm] = unresolved[nm]
                    pending.discard(nm)
                    progressed = True
                    continue
                try:
                    r[nm] = ev(trees[nm], r)
                except KeyError as e:
                    r[nm] = f"#REF!({e.args[0]})"
                pending.discard(nm)
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
    _eval_plain(
        seq,
        plain,
        later=frozenset(formulas) - frozenset(plain),
        computed=frozenset(formulas),
        cols=frozenset(cols),
    )
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

    _eval_plain(seq, plain, computed=frozenset(formulas), cols=frozenset(cols))
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
