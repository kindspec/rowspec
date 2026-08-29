"""rowspec — a second, independent implementation, written from SPEC.md.

Entry points: parse, structure, evaluate, render, canon, set_cell, Malformed.
Standard library only.
"""

import re
import unicodedata

__all__ = [
    "Malformed",
    "parse",
    "structure",
    "evaluate",
    "render",
    "canon",
    "set_cell",
]


class Malformed(Exception):
    """Every refusal in SPEC.md §9 (plus §3's identifier rules) raises this."""


# --------------------------------------------------------------------------
# values
# --------------------------------------------------------------------------


class _Blank:
    _inst = None

    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst

    def __repr__(self):
        return "BLANK"


BLANK = _Blank()


class TextVal:
    __slots__ = ("s",)

    def __init__(self, s):
        self.s = s

    def __eq__(self, o):
        return isinstance(o, TextVal) and o.s == self.s

    def __hash__(self):
        return hash(("text", self.s))

    def __repr__(self):
        return f"TEXT({self.s!r})"


class Ref:
    """A propagating #REF! error carrying the name that broke."""

    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def __eq__(self, o):
        return isinstance(o, Ref) and o.name == self.name

    def __hash__(self):
        return hash(("ref", self.name))

    def __repr__(self):
        return f"#REF!({self.name})"


def display(v):
    """External representation used in the rows / aggregates the API returns."""
    if isinstance(v, Ref):
        return f"#REF!({v.name})"
    if v is BLANK:
        return ""
    if isinstance(v, TextVal):
        return v.s
    return v


# --------------------------------------------------------------------------
# lexical helpers
# --------------------------------------------------------------------------

# SPEC.md §8: "thousands separators, parenthesised negatives, and non-ASCII
# spaces are refused rather than interpreted".  ASCII digits only -- \d in
# Python matches Unicode decimal digits, which would silently accept e.g.
# Arabic-Indic numerals.
NUMBER_RE = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)$")
# §6: date is "Y-M-D or Y/M/D".
DATE_RE = re.compile(r"^[0-9]{4}([-/])[0-9]{1,2}\1[0-9]{1,2}$")
ALIGN_CELL_RE = re.compile(r"^:?-+:?$")

CONFLICT_RE = re.compile(r"^(<{7}|={7}|>{7}|\|{7})(\s|$)")

AGG_FUNCS = ("sum", "count", "min", "max", "avg")
ROWREL_FUNCS = ("cumulative", "prior", "delta")


def nfc(s):
    return unicodedata.normalize("NFC", s)


def check_identifier(name, what):
    if name == "":
        raise Malformed(f"malformed declaration: empty {what} name")
    for ch in name:
        if unicodedata.category(ch) == "Cf":
            raise Malformed(f"format character U+{ord(ch):04X} in {what} identifier {name!r}")
    return nfc(name)


def coerce_cell(raw):
    """Turn a raw cell's text into a value.  Padding is ASCII-space only."""
    s = raw.strip(" \t\r")
    if s == "":
        return BLANK
    if NUMBER_RE.match(s):
        f = float(s)
        if f != f or f in (float("inf"), float("-inf")):
            return TextVal(s)
        return f
    return TextVal(s)


# --------------------------------------------------------------------------
# expression AST + parser
# --------------------------------------------------------------------------

TOKEN_RE = re.compile(
    r"""
    (?P<ws>[ \t]+)
  | (?P<num>[0-9]+(?:\.[0-9]*)?|\.[0-9]+)
  | (?P<str>"[^"]*")
  | (?P<path>[\w./-]*\.mdtbl)
  | (?P<id>[^\W\d]\w*)
  | (?P<op>[-+*/(),=@])
""",
    re.VERBOSE | re.UNICODE,
)


def tokenize(src, ctx):
    toks = []
    i = 0
    while i < len(src):
        m = TOKEN_RE.match(src, i)
        if not m:
            raise Malformed(f"{ctx}: unexpected character {src[i]!r}")
        i = m.end()
        if m.lastgroup == "ws":
            continue
        toks.append((m.lastgroup, m.group()))
    return toks


class P:
    def __init__(self, toks, ctx):
        self.t = toks
        self.i = 0
        self.ctx = ctx

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def next(self):
        tok = self.peek()
        self.i += 1
        return tok

    def expect_op(self, op):
        k, v = self.next()
        if k != "op" or v != op:
            raise Malformed(f"{self.ctx}: expected {op!r}")

    def at_end(self):
        return self.i >= len(self.t)

    def fail(self, msg="unparseable expression"):
        raise Malformed(f"{self.ctx}: {msg}")


def parse_expr(p):
    node = parse_term(p)
    while True:
        k, v = p.peek()
        if k == "op" and v in "+-":
            p.next()
            node = ("bin", v, node, parse_term(p))
        else:
            return node


def parse_term(p):
    node = parse_unary(p)
    while True:
        k, v = p.peek()
        if k == "op" and v in "*/":
            p.next()
            node = ("bin", v, node, parse_unary(p))
        else:
            return node


def parse_unary(p):
    k, v = p.peek()
    if k == "op" and v in "+-":
        p.next()
        return ("neg", parse_unary(p)) if v == "-" else parse_unary(p)
    return parse_primary(p)


def parse_primary(p):
    k, v = p.next()
    if k == "num":
        return ("lit", float(v))
    if k == "str":
        return ("str", v[1:-1])
    if k == "op" and v == "(":
        node = parse_expr(p)
        p.expect_op(")")
        return node
    if k == "op" and v == "@":
        k2, v2 = p.next()
        if k2 != "id":
            p.fail("@ must be followed by a column name")
        return ("at", nfc(v2))
    if k == "path":
        return ("path", v)
    if k == "id":
        k2, v2 = p.peek()
        if k2 == "op" and v2 == "(":
            return parse_call(p, v)
        if v in ("where", "and"):
            p.fail(f"unexpected keyword {v!r}")
        return ("col", nfc(v))
    p.fail()


def parse_call(p, fname):
    p.expect_op("(")
    low = fname.lower()
    if low in ROWREL_FUNCS:
        k, v = p.next()
        if k != "id":
            p.fail(f"{low}() takes a column name")
        p.expect_op(")")
        return ("rowrel", low, nfc(v))
    if low in AGG_FUNCS:
        k, v = p.next()
        if k != "id" or v in ("where", "and"):
            p.fail(f"{low}() takes a column name")
        col = nfc(v)
        preds = []
        k2, v2 = p.peek()
        if k2 == "id" and v2 == "where":
            p.next()
            while True:
                k3, v3 = p.next()
                if k3 != "id" or v3 in ("where", "and"):
                    p.fail("predicate needs a column name")
                p.expect_op("=")
                preds.append((nfc(v3), parse_primary(p)))
                k4, v4 = p.peek()
                if k4 == "id" and v4 == "and":
                    p.next()
                    continue
                break
        p.expect_op(")")
        return ("agg", low, col, tuple(preds))
    if low == "lookup":
        args = []
        while True:
            k, v = p.next()
            if k is None:
                p.fail("unterminated lookup()")
            if k == "op" and v == ")":
                break
            if k in ("id", "path"):
                args.append(v)
        if len(args) != 3:
            p.fail("lookup() takes (file, key column, wanted column)")
        return ("lookup", args[0], nfc(args[1]), nfc(args[2]))
    # §7 "An unknown function is refused."  §9.11 calls it an unknown
    # aggregate function; one message satisfies both.
    raise Malformed(f"unknown aggregate function {fname!r}")


def parse_formula(src, ctx):
    toks = tokenize(src, ctx)
    if not toks:
        raise Malformed(f"{ctx}: empty formula")
    p = P(toks, ctx)
    node = parse_expr(p)
    if not p.at_end():
        p.fail("trailing tokens")
    return node


def walk(node):
    yield node
    if node[0] == "bin":
        yield from walk(node[2])
        yield from walk(node[3])
    elif node[0] == "neg":
        yield from walk(node[1])
    elif node[0] == "agg":
        for _, lit in node[3]:
            yield from walk(lit)


# --------------------------------------------------------------------------
# line model
# --------------------------------------------------------------------------


class Line:
    __slots__ = ("body", "term", "cells", "trailing_pipe", "tail", "kind")

    def __init__(self, body, term):
        self.body = body
        self.term = term
        self.cells = None
        self.trailing_pipe = False
        self.tail = ""
        self.kind = "other"

    def text(self):
        if self.cells is None:
            return self.body + self.term
        inner = "|".join(self.cells)
        return "|" + inner + ("|" if self.trailing_pipe else "") + self.tail + self.term


def split_lines(text):
    out = []
    i = 0
    n = len(text)
    while i < n:
        j = text.find("\n", i)
        if j < 0:
            out.append(Line(text[i:], ""))
            break
        body = text[i:j]
        term = "\n"
        if body.endswith("\r"):
            body = body[:-1]
            term = "\r\n"
        out.append(Line(body, term))
        i = j + 1
    return out


def split_cells(line):
    body = line.body
    # Trailing whitespace after the closing pipe is decoration, not a field:
    # canon/idempotent-trailing-spaces requires canon() to drop it while
    # roundtrip requires render() to give it back.  SPEC.md never says so.
    stripped = body.rstrip(" \t")
    if stripped.endswith("|") and len(stripped) > 1:
        line.trailing_pipe = True
        line.tail = body[len(stripped) :]
        inner = stripped[1:-1]
    else:
        line.trailing_pipe = False
        line.tail = ""
        inner = body[1:]
    line.cells = inner.split("|")


def is_align_row(cells):
    return all(ALIGN_CELL_RE.match(c.strip(" \t\r")) for c in cells)


# --------------------------------------------------------------------------
# structure
# --------------------------------------------------------------------------


class Column:
    __slots__ = ("name", "raw_name", "formula", "src")

    def __init__(self, name, raw_name, formula, src):
        self.name = name
        self.raw_name = raw_name
        self.formula = formula
        self.src = src

    @property
    def computed(self):
        return self.formula is not None


class Structure:
    def __init__(self):
        self.deferred = None
        self.lines = []
        self.columns = []
        self.col_index = {}
        self.row_lines = []  # Line objects, file order
        self.key = None  # column name or None
        self.order = None  # column name or None
        self.aggregates = []  # (name, node)
        self.header_line = None
        self.align_line = None

    def cell(self, row_i, col_name):
        return self.row_lines[row_i].cells[self.col_index[col_name]]


def structure(text):
    st = Structure()
    st.deferred = None
    # §3: UTF-8, LF line endings, no BOM.  A BOM stops the file being a table
    # at all, so it is refused eagerly.
    if text.startswith("\ufeff"):
        raise Malformed("byte order mark at the start of the file")
    st.lines = split_lines(text)
    # CR is refused too -- but roundtrip/crlf requires structure() to hand
    # back a byte-exact document, so the diagnostic is *reported* here and
    # *raised* by evaluate() (§9's "reported separately from being handled").
    for ln in st.lines:
        if "\r" in ln.body:
            st.deferred = Malformed("lone carriage return in a line")
            break
        if ln.term == "\r\n":
            st.deferred = Malformed("CRLF line endings; §3 requires LF")
            break

    # §9.1 -- conflict markers anywhere in the file, checked before anything
    # else because `|||||||` would otherwise read as a table row.
    for ln in st.lines:
        if CONFLICT_RE.match(ln.body):
            raise Malformed(f"conflict marker in file: {ln.body[:20]!r}")

    # §4 -- the table is a contiguous run of lines beginning with '|'.
    start = None
    for i, ln in enumerate(st.lines):
        if ln.body.startswith("|"):
            start = i
            break
    if start is None:
        raise Malformed("file contains no table")
    end = start
    while end < len(st.lines) and st.lines[end].body.startswith("|"):
        end += 1

    for ln in st.lines[:start]:
        s = ln.body.strip()
        if s and not s.startswith("#"):
            raise Malformed(f"malformed declaration before the table: {ln.body!r}")

    if end - start < 2:
        raise Malformed("file contains no table: header and alignment row required")

    for ln in st.lines[start:end]:
        split_cells(ln)

    header, align = st.lines[start], st.lines[start + 1]
    header.kind, align.kind = "header", "align"
    ncol = len(header.cells)

    # §9.7 -- alignment row field count
    if len(align.cells) != ncol:
        raise Malformed(f"alignment row has {len(align.cells)} fields, header has {ncol}")
    if not is_align_row(align.cells):
        raise Malformed(f"alignment row is not an alignment row: {align.body!r}")

    # §5 -- header cells
    seen = {}
    for c in header.cells:
        raw = c.strip(" \t\r")
        if "=" in raw:
            nm, fm = raw.split("=", 1)
            nm, fm = nm.strip(), fm.strip()
        else:
            nm, fm = raw, None
        name = check_identifier(nm, "column")
        if name in seen:
            raise Malformed(f"duplicate column name {name!r}")
        seen[name] = True
        node = parse_formula(fm, f"column {name}") if fm is not None else None
        if fm is not None and fm == "":
            raise Malformed(f"column {name}: empty formula")
        st.columns.append(Column(name, nm, node, fm))
    st.col_index = {c.name: i for i, c in enumerate(st.columns)}

    # data rows
    for ln in st.lines[start + 2 : end]:
        ln.kind = "data"
        if is_align_row(ln.cells):
            # §9.8
            raise Malformed(f"alignment-style row among the data rows: {ln.body!r}")
        if len(ln.cells) != ncol:
            raise Malformed(f"data row has {len(ln.cells)} fields, header has {ncol}")
        st.row_lines.append(ln)

    # §5: "A column with a formula is COMPUTED and its data cells are empty."
    for c in st.columns:
        if not c.computed:
            continue
        j = st.col_index[c.name]
        for ln in st.row_lines:
            if ln.cells[j].strip(" \t\r") != "":
                raise Malformed(
                    f"computed column {c.name!r} holds a stored value {ln.cells[j].strip()!r}"
                )

    # declarations
    for ln in st.lines[end:]:
        parse_declaration(st, ln)

    validate(st)
    return st


def parse_declaration(st, ln):
    s = ln.body
    # The one ignorable channel (§9): '#' comments.  The spec never gives its
    # syntax; '#' is taken from the example in §6.
    hash_i = s.find("#")
    if hash_i >= 0:
        s = s[:hash_i]
    s = s.strip()
    if s == "":
        return
    if ":=" not in s:
        raise Malformed(f"malformed declaration: {ln.body!r}")
    lhs, rhs = s.split(":=", 1)
    lhs, rhs = lhs.strip(), rhs.strip()
    if lhs == "" or rhs == "":
        raise Malformed(f"malformed declaration: {ln.body!r}")
    ln.kind = "decl"

    if lhs == "key":
        if st.key is not None:
            raise Malformed("duplicate key declaration")
        toks = tokenize(rhs, "key declaration")
        if len(toks) != 1 or toks[0][0] != "id":
            raise Malformed(f"malformed declaration: key := {rhs!r}")
        st.key = check_identifier(toks[0][1], "column")
        return

    if lhs == "order":
        if st.order is not None:
            raise Malformed("duplicate order declaration")
        m = re.match(r"^by\(\s*([^\W\d]\w*)\s*\)$", rhs, re.UNICODE)
        if not m:
            raise Malformed(f"malformed declaration: order := {rhs!r}")
        st.order = check_identifier(m.group(1), "column")
        return

    name = check_identifier(lhs, "aggregate")
    if any(name == n for n, _ in st.aggregates):
        raise Malformed(f"duplicate aggregate name {name!r}")
    node = parse_formula(rhs, f"aggregate {name}")
    if node[0] != "agg":
        raise Malformed(f"malformed declaration: {ln.body!r} is not an aggregate over a column")
    for sub in walk(node):
        if sub[0] == "at":
            raise Malformed(
                f"malformed declaration: @{sub[1]} has no current row in a table-level aggregate"
            )
        if sub[0] == "rowrel":
            raise Malformed(f"malformed declaration: {sub[1]}() is a row-relative operator")
    st.aggregates.append((name, node))


def validate(st):
    names = set(st.col_index)

    if st.key is not None and st.key not in names:
        raise Malformed(f"key := {st.key} names no column")
    if st.key is not None and st.columns[st.col_index[st.key]].computed:
        raise Malformed(f"key := {st.key} is a computed column")

    # §9.5 -- duplicate row id, where a key is declared
    if st.key is not None:
        ki = st.col_index[st.key]
        seen = {}
        for ln in st.row_lines:
            v = nfc(ln.cells[ki].strip(" \t\r"))
            if v in seen:
                raise Malformed(f"duplicate key {v!r}")
            seen[v] = True

    # §9.9 -- row-relative operator with no declared order
    uses_rowrel = any(
        sub[0] == "rowrel" for c in st.columns if c.computed for sub in walk(c.formula)
    )
    if uses_rowrel and st.order is None:
        raise Malformed("row-relative operator requires a declared row order")

    # §9.10 -- order column must be stored, single-typed, finite
    if st.order is not None:
        if st.order not in names:
            raise Malformed(f"order := by({st.order}) names no column")
        col = st.columns[st.col_index[st.order]]
        if col.computed:
            raise Malformed(f"order := by({st.order}) is a computed column")
        if st.key is None:
            raise Malformed("order requires a declared key")
        kinds = set()
        oi = st.col_index[st.order]
        for ln in st.row_lines:
            kinds.add(order_kind(ln.cells[oi].strip(" \t\r")))
        if len(kinds) > 1:
            raise Malformed(
                "order := by({}) mixes types: {}".format(st.order, ", ".join(sorted(kinds)))
            )

    # referenced-but-unknown column names are NOT a refusal: §8 makes them
    # #REF! at evaluation time.


NONFINITE = {"inf", "+inf", "-inf", "infinity", "+infinity", "-infinity", "nan", "+nan", "-nan"}


def order_kind(s):
    if s == "":
        return "blank"
    if s.lower() in NONFINITE:
        raise Malformed(f"order column holds a non-finite number {s!r}")
    if NUMBER_RE.match(s):
        f = float(s)
        if f != f or f in (float("inf"), float("-inf")):
            raise Malformed(f"order column holds a non-finite number {s!r}")
        return "number"
    if DATE_RE.match(s):
        return "date"
    return "text"


def parse(text):
    """Recognition only; identical algorithm to structure() (§9)."""
    return structure(text)


# --------------------------------------------------------------------------
# render / canon / set_cell
# --------------------------------------------------------------------------


def render(st):
    return "".join(ln.text() for ln in st.lines)


def canon_align(cell):
    s = cell.strip(" \t\r")
    left = s.startswith(":")
    right = s.endswith(":") and len(s) > 1
    return (":" if left else "-") + "-" + (":" if right else "-")


def canon(text):
    st = structure(text)
    for ln in st.lines:
        if ln.cells is None:
            continue
        if ln.kind == "align":
            cells = [canon_align(c) for c in ln.cells]
        else:
            cells = [c.strip(" \t\r") for c in ln.cells]
        ln.cells = [" " + c + " " for c in cells]
        ln.trailing_pipe = True
        ln.tail = ""
    return render(st)


def set_cell(st, row_key, column, value):
    col = nfc(column)
    if col not in st.col_index:
        raise Malformed(f"no column named {column!r}")
    if st.columns[st.col_index[col]].computed:
        raise Malformed(f"cannot write a value into the computed column {column!r}")
    if st.key is None:
        raise Malformed("cannot address a row: no key is declared")
    ki = st.col_index[st.key]
    want = nfc(str(row_key))
    for ln in st.row_lines:
        if nfc(ln.cells[ki].strip(" \t\r")) == want:
            ln.cells[st.col_index[col]] = f" {value} "
            return st
    raise Malformed(f"no row with key {row_key!r}")


# --------------------------------------------------------------------------
# evaluation
# --------------------------------------------------------------------------


def sort_key_for(kind, s, key):
    if kind == "number":
        return (float(s), key)
    if kind == "date":
        sep = "-" if "-" in s else "/"
        y, m, d = s.split(sep)
        return ((int(y), int(m), int(d)), key)
    if kind == "blank":
        return ("", key)
    return (s, key)


class Evaluator:
    def __init__(self, st):
        self.st = st
        self.n = len(st.row_lines)
        self.cache = {}
        self.stack = []

        # derived order (§6): the tuple (typed value of c, key), never a
        # string concatenation.
        if st.order is not None and self.n:
            oi = st.col_index[st.order]
            ki = st.col_index[st.key]
            kinds = {order_kind(ln.cells[oi].strip(" \t\r")) for ln in st.row_lines}
            kind = kinds.pop()
            decorated = []
            for i, ln in enumerate(st.row_lines):
                ov = ln.cells[oi].strip(" \t\r")
                kv = nfc(ln.cells[ki].strip(" \t\r"))
                decorated.append((sort_key_for(kind, ov, kv), i))
            decorated.sort(key=lambda t: t[0])
            self.perm = [i for _, i in decorated]
        else:
            self.perm = list(range(self.n))
        self.pos = [0] * self.n
        for p, i in enumerate(self.perm):
            self.pos[i] = p

    # -- columns ---------------------------------------------------------

    def column(self, name):
        """Values of `name` for every row, indexed by DERIVED position."""
        if name in self.cache:
            return self.cache[name]
        if name not in self.st.col_index:
            return None
        if name in self.stack:
            vals = [Ref(name)] * self.n  # cycle: stay total (§8)
            self.cache[name] = vals
            return vals
        col = self.st.columns[self.st.col_index[name]]
        idx = self.st.col_index[name]
        self.stack.append(name)
        try:
            if not col.computed:
                vals = [coerce_cell(self.st.row_lines[i].cells[idx]) for i in self.perm]
            else:
                vals = [self.eval(col.formula, p) for p in range(self.n)]
        finally:
            self.stack.pop()
        self.cache[name] = vals
        return vals

    def ref_value(self, name, p):
        """A bare column reference inside arithmetic (§8)."""
        vals = self.column(name)
        if vals is None:
            return Ref(name)
        v = vals[p]
        if isinstance(v, Ref):
            return v
        if v is BLANK or isinstance(v, TextVal):
            # a blank cell is not zero; a value that will not coerce is #REF!
            return Ref(name)
        return v

    # -- expressions -----------------------------------------------------

    def eval(self, node, p):
        t = node[0]
        if t == "lit":
            return node[1]
        if t == "str":
            return TextVal(node[1])
        if t == "col":
            return self.ref_value(node[1], p)
        if t == "at":
            # SPEC.md 7: "@c means *this row's* value of c".  It is compared
            # for equality, not arithmetic, so it is NOT coerced to a number
            # -- otherwise no text column could ever be grouped on.
            vals = self.column(node[1])
            return Ref(node[1]) if vals is None else vals[p]
        if t == "path":
            return TextVal(node[1])
        if t == "neg":
            v = self.eval(node[1], p)
            return v if isinstance(v, Ref) else -v
        if t == "bin":
            a = self.eval(node[2], p)
            if isinstance(a, Ref):
                return a
            b = self.eval(node[3], p)
            if isinstance(b, Ref):
                return b
            op = node[1]
            if op == "+":
                return a + b
            if op == "-":
                return a - b
            if op == "*":
                return a * b
            if b == 0:
                return Ref("division by zero")
            return a / b
        if t == "lookup":
            # §7 defines lookup(); §8 forbids I/O and evaluate() is handed
            # only this artifact's bytes, so the target row is always absent
            # and the defined result is #REF!(file[key]).
            kv = self.column(node[2])
            k = "" if kv is None else display(kv[p])
            return Ref(f"{node[1]}[{k}]")
        if t == "rowrel":
            return self.rowrel(node[1], node[2], p)
        if t == "agg":
            return self.aggregate(node[1], node[2], node[3], p)
        raise Malformed(f"unevaluable expression node {node!r}")

    def numeric_column(self, name):
        vals = self.column(name)
        if vals is None:
            return None
        out = []
        for v in vals:
            if isinstance(v, Ref):
                out.append(v)
            elif v is BLANK:
                out.append(BLANK)
            elif isinstance(v, TextVal):
                out.append(Ref(name))
            else:
                out.append(v)
        return out

    def rowrel(self, fn, name, p):
        vals = self.numeric_column(name)
        if vals is None:
            return Ref(name)
        if fn == "prior":
            return BLANK if p == 0 else vals[p - 1]
        if fn == "delta":
            if p == 0:
                return BLANK
            a, b = vals[p], vals[p - 1]
            if isinstance(a, Ref):
                return a
            if isinstance(b, Ref):
                return b
            if a is BLANK:
                return Ref(name)
            if b is BLANK:
                return Ref(name)
            return a - b
        # cumulative
        total = 0.0
        for i in range(p + 1):
            v = vals[i]
            if isinstance(v, Ref):
                return v
            if v is BLANK:
                return Ref(name)
            total += v
        return total

    def matches(self, preds, cand, cur):
        """cand: the row being tested.  cur: the row whose @refs we resolve."""
        for cname, litnode in preds:
            vals = self.column(cname)
            if vals is None:
                return Ref(cname)
            want = self.eval(litnode, cur)
            if isinstance(want, Ref):
                return want
            got = vals[cand]
            if isinstance(got, Ref):
                return got
            if not equal(got, want):
                return False
        return True

    def aggregate(self, fn, name, preds, p):
        # Every aggregate reads its column numerically -- eval/ref-poisons-
        # every-aggregate makes even count() inherit a #REF! from an
        # uncoercible cell.
        vals = self.numeric_column(name)
        if vals is None:
            return Ref(name)
        rows = []
        for q in range(self.n):
            m = self.matches(preds, q, p) if preds else True
            if isinstance(m, Ref):
                return m
            if m:
                rows.append(vals[q])
        # §8: an aggregate over any column containing a #REF! is itself #REF!
        for v in rows:
            if isinstance(v, Ref):
                return v
        if fn == "count":
            return len(rows)
        nums = [v for v in rows if v is not BLANK]
        if fn == "sum":
            return sum(nums) if nums else 0.0
        if not nums:
            return BLANK
        if fn == "min":
            return min(nums)
        if fn == "max":
            return max(nums)
        return sum(nums) / len(nums)


def equal(a, b):
    if isinstance(a, TextVal) and isinstance(b, TextVal):
        return nfc(a.s) == nfc(b.s)
    if isinstance(a, TextVal) and isinstance(b, float):
        return NUMBER_RE.match(a.s) is not None and float(a.s) == b
    if isinstance(b, TextVal) and isinstance(a, float):
        return NUMBER_RE.match(b.s) is not None and float(b.s) == a
    if a is BLANK or b is BLANK:
        return a is b
    return a == b


def evaluate(text):
    st = structure(text)
    if st.deferred is not None:
        raise st.deferred
    ev = Evaluator(st)

    rows = []
    for i, ln in enumerate(st.row_lines):
        p = ev.pos[i]
        row = {}
        for c in st.columns:
            if c.computed:
                row[c.name] = display(ev.column(c.name)[p])
            else:
                row[c.name] = ln.cells[st.col_index[c.name]].strip(" \t\r")
        rows.append(row)

    aggs = {}
    for name, node in st.aggregates:
        aggs[name] = display(ev.eval(node, 0))
    return rows, aggs
