"""rowspec — a second, independent implementation, written from SPEC.md.

Entry points: parse, structure, evaluate, render, canon, set_cell, Malformed.
Standard library only.  Every non-obvious decision cites the clause it came
from; where the prose did not determine the answer the comment says so.
"""

import os
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
    """Every refusal in SPEC.md §9."""


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
    """A propagating #REF! error carrying the name that broke (§8)."""

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
    if isinstance(v, Ref):
        return f"#REF!({v.name})"
    if v is BLANK:
        return ""
    if isinstance(v, TextVal):
        return v.s
    return v


def as_text(v):
    """Text form of a value, for key comparison across a lookup."""
    if v is BLANK:
        return ""
    if isinstance(v, TextVal):
        return v.s
    if isinstance(v, Ref):
        return f"#REF!({v.name})"
    if float(v).is_integer():
        return str(int(v))
    return repr(float(v))


# --------------------------------------------------------------------------
# §4.1 lexical layer
# --------------------------------------------------------------------------

WSP = " \t"

# §4.1.6: number = [ "-" ] 1*DIGIT [ "." 1*DIGIT ]; DIGIT is U+0030-U+0039 and
# nothing else.  A leading "+", an exponent, ".5", "5." and any digit grouping
# are refused and are therefore text.
NUMBER_RE = re.compile(r"^-?[0-9]+(?:\.[0-9]+)?$")

# §4.1.7: 1*4DIGIT sep 1*2DIGIT sep 1*2DIGIT, both separators the same.
DATE_RE = re.compile(r"^[0-9]{1,4}([-/])[0-9]{1,2}\1[0-9]{1,2}$")

# §4.1.5: align-cell = [ ":" ] 1*"-" [ ":" ]
ALIGN_CELL_RE = re.compile(r"^:?-+:?$")

# §4.1.9: ident = 1*( LETTER / MARK / NUM / "_" / "-" / "." )
IDENT_EXTRA = "_-."

# §4.1.7 / §9.10: non-finite spellings are never numbers and are refused in an
# order column in any case.
NONFINITE = {"inf", "+inf", "-inf", "infinity", "+infinity", "-infinity", "nan", "+nan", "-nan"}

CONFLICT_PREFIXES = ("<" * 7, "=" * 7, ">" * 7, "|" * 7)

# §4.1: table-line = *WSP "|" 1*( cell "|" ) *WSP.  Both pipes required; a cell
# can never contain "|" because no escape exists (§4.1.3).
TABLE_LINE_RE = re.compile(r"^[ \t]*\|(?:[^|]*\|)+[ \t]*$")

AGG_FUNCS = ("sum", "count", "min", "max", "avg")
ROWREL_FUNCS = ("cumulative", "prior", "delta")


def nfc(s):
    return unicodedata.normalize("NFC", s)


def is_ident(name):
    """§4.1.9 -- an allowlist, so an unforeseen character is refused."""
    if not name:
        return False
    for ch in name:
        if ch in IDENT_EXTRA:
            continue
        if unicodedata.category(ch)[0] not in ("L", "M", "N"):
            return False
    return True


def check_identifier(name, what):
    """§9.16.  Whitespace and Cf are excluded by `ident` by construction."""
    if not is_ident(name):
        raise Malformed(
            f"{what} identifier {name!r} is not an ident (§4.1.9): whitespace, a Cf "
            "format character, or a character outside the allowlist"
        )
    return nfc(name)


def trim(s):
    """§4/§4.1.4: leading and trailing ASCII space and horizontal tab, and
    nothing else.  U+00A0 and friends in padding position are thousands
    separators, not padding."""
    return s.strip(WSP)


def coerce_cell(raw):
    s = trim(raw)
    if s == "":
        return BLANK
    if NUMBER_RE.match(s):
        return float(s)
    return TextVal(s)


# --------------------------------------------------------------------------
# formula expressions
#
# §4.1 gives a grammar for declarations but NOT for the expression language in
# a header cell -- no operators, no precedence, no literals, no `@`, no path.
# What follows is this implementation's reading, flagged in the findings.
# --------------------------------------------------------------------------

TOKEN_RE = re.compile(
    r"""
    (?P<ws>[ \t]+)
  | (?P<path>[0-9A-Za-z_./-]*\.mdtbl)
  | (?P<num>[0-9]+(?:\.[0-9]+)?)
  | (?P<str>"[^"]*")
  | (?P<id>[^\W\d][\w.]*)
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
        inner = parse_unary(p)
        return ("neg", inner) if v == "-" else inner
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
        return ("at", want_colname(p, "@ must be followed by a column name"))
    if k == "id":
        k2, v2 = p.peek()
        if k2 == "op" and v2 == "(":
            return parse_call(p, v)
        if v in ("where", "and"):
            p.fail(f"unexpected keyword {v!r}")
        return ("col", check_identifier(v, "column"))
    p.fail()


def want_colname(p, what):
    """A column-name position.  §4.1.9 makes `123` a well-formed ident, and the
    declaration grammar has no numeric-literal alternative, so a bare number
    here is a column name -- while in an arithmetic operand position §4.1.6
    makes it a literal.  §4.1 does not resolve that; see the findings."""
    k, v = p.next()
    if k in ("id", "num") and v not in ("where", "and"):
        return check_identifier(v, "column")
    p.fail(what)


def parse_call(p, fname):
    p.expect_op("(")
    low = fname.lower()
    if low in ROWREL_FUNCS:
        name = want_colname(p, f"{low}() takes a column name")
        p.expect_op(")")
        return ("rowrel", low, name)
    if low in AGG_FUNCS:
        return parse_agg_tail(p, low)
    if low == "lookup":
        # §7: "The target is a **literal** path written in the formula ... It
        # is never computed at evaluation time."  So argument 1 must be a
        # single path token; `stem + ".mdtbl"` is refused here.
        k, v = p.next()
        if k not in ("path", "str"):
            p.fail(
                "lookup() target must be a literal path written in the formula, never computed (§7)"
            )
        path = v[1:-1] if k == "str" else v
        p.expect_op(",")
        kc = want_colname(p, "lookup() takes (path, key column, wanted column)")
        p.expect_op(",")
        wc = want_colname(p, "lookup() takes (path, key column, wanted column)")
        p.expect_op(")")
        return ("lookup", path, kc, wc)
    # §7 "An unknown function is refused."  §9.11 names it.
    raise Malformed(f"unknown aggregate function {fname!r}")


def parse_agg_tail(p, low):
    col = want_colname(p, f"{low}() takes a column name")
    preds = []
    k2, v2 = p.peek()
    if k2 == "id" and v2 == "where":
        p.next()
        while True:
            lhs = want_colname(p, "predicate needs a column name")
            p.expect_op("=")
            preds.append((lhs, parse_primary(p)))
            k4, v4 = p.peek()
            if k4 == "id" and v4 == "and":
                p.next()
                continue
            break
    p.expect_op(")")
    return ("agg", low, col, tuple(preds))


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
# lines and classification (§4.1)
# --------------------------------------------------------------------------


class Line:
    __slots__ = ("body", "term", "kind", "cells", "head", "tail")

    def __init__(self, body, term):
        self.body = body
        self.term = term
        self.kind = None
        self.cells = None
        self.head = ""
        self.tail = ""

    def text(self):
        if self.cells is None:
            return self.body + self.term
        return self.head + "|" + "|".join(self.cells) + "|" + self.tail + self.term


def split_lines(text):
    """LF and CRLF are both `eol` (§4.1).  A lone CR is refused (§9.15)."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        j = text.find("\n", i)
        if j < 0:
            body, term = text[i:], ""
            i = n
        else:
            body, term = text[i:j], "\n"
            if body.endswith("\r"):
                body, term = body[:-1], "\r\n"
            i = j + 1
        if "\r" in body:
            raise Malformed("lone CR in a line (§9.15): it makes two rows share one git line")
        out.append(Line(body, term))
    return out


def classify(line):
    """§4.1: the alternatives of `line` are tried in the order written and the
    first that matches decides.  `conflict` precedes `table-line` because
    `|||||||` is itself a well-formed seven-cell table line."""
    b = line.body
    if b[:7] in CONFLICT_PREFIXES:
        return "conflict"
    stripped = b.lstrip(WSP)
    if stripped.startswith("#"):
        return "annotation"
    if TABLE_LINE_RE.match(b):
        return "table"
    if stripped == "":
        return "blank"
    return "declaration"  # provisional; validated in parse_declaration


def split_cells(line):
    b = line.body
    lead = len(b) - len(b.lstrip(WSP))
    line.head = b[:lead]
    rest = b[lead:]
    trail = len(rest) - len(rest.rstrip(WSP))
    line.tail = rest[len(rest) - trail :] if trail else ""
    core = rest[: len(rest) - trail] if trail else rest
    # core is "|" + (cell "|")+
    line.cells = core[1:-1].split("|")


def is_align_row(cells):
    return bool(cells) and all(ALIGN_CELL_RE.match(trim(c)) for c in cells)


# --------------------------------------------------------------------------
# structure
# --------------------------------------------------------------------------


class Column:
    __slots__ = ("name", "formula")

    def __init__(self, name, formula):
        self.name = name
        self.formula = formula

    @property
    def computed(self):
        return self.formula is not None


class Structure:
    def __init__(self):
        self.lines = []
        self.columns = []
        self.col_index = {}
        self.row_lines = []
        self.key = None
        self.order = None
        self.aggregates = []


def structure(text):
    st = Structure()

    # §9.14 -- a leading BOM, or bytes that are not well-formed UTF-8.  The
    # caller decodes, so a BOM survives as U+FEFF.
    if text.startswith("﻿"):
        raise Malformed("leading BOM (§9.14)")

    st.lines = split_lines(text)

    for ln in st.lines:
        ln.kind = classify(ln)

    # §9.1 -- conflict markers anywhere, before any other classification.
    for ln in st.lines:
        if ln.kind == "conflict":
            raise Malformed(f"conflict marker (§9.1): {ln.body[:16]!r}")

    # §4.1.2 -- the table is the MAXIMAL CONTIGUOUS RUN of table-lines, and a
    # file has exactly one table.  A table line outside that run is refused
    # (§9.19).
    idx = [i for i, ln in enumerate(st.lines) if ln.kind == "table"]
    if not idx:
        raise Malformed("file contains no table (§9.13)")
    start = idx[0]
    end = start
    while end < len(st.lines) and st.lines[end].kind == "table":
        end += 1
    for i in idx:
        if not (start <= i < end):
            raise Malformed(
                "table line after the table's contiguous run has ended "
                f"(§9.19): {st.lines[i].body[:40]!r}"
            )

    for ln in st.lines[start:end]:
        split_cells(ln)

    # §9.20 -- a table shorter than two lines, or a second line that is not a
    # valid alignment row.  Never reinterpreted as a data row (§4).
    if end - start < 2:
        raise Malformed("table is shorter than two lines: no alignment row (§9.20)")
    header, align = st.lines[start], st.lines[start + 1]
    header.kind, align.kind = "header", "align"
    ncol = len(header.cells)
    if len(align.cells) != ncol:
        raise Malformed(f"alignment row has {len(align.cells)} fields, header has {ncol} (§9.7)")
    if not is_align_row(align.cells):
        raise Malformed(
            f"second table line is not a valid alignment row (§9.20): {align.body[:60]!r}"
        )

    # §5 -- header cells
    seen = set()
    for c in header.cells:
        raw = trim(c)
        if "=" in raw:
            nm, fm = raw.split("=", 1)
            nm, fm = trim(nm), trim(fm)
        else:
            nm, fm = raw, None
        name = check_identifier(nm, "column")
        if name in seen:
            raise Malformed(f"duplicate column name {name!r} (§9.2)")
        seen.add(name)
        node = None
        if fm is not None:
            if fm == "":
                raise Malformed(f"column {name}: empty formula")
            node = parse_formula(fm, f"column {name}")
        st.columns.append(Column(name, node))
    st.col_index = {c.name: i for i, c in enumerate(st.columns)}

    # data rows
    for ln in st.lines[start + 2 : end]:
        ln.kind = "data"
        if is_align_row(ln.cells):
            raise Malformed(f"alignment-style row among the data rows (§9.8): {ln.body[:60]!r}")
        if len(ln.cells) != ncol:
            raise Malformed(f"data row has {len(ln.cells)} fields, header has {ncol} (§9.6)")
        st.row_lines.append(ln)

    # §9.17 -- a value in a computed cell
    for c in st.columns:
        if not c.computed:
            continue
        j = st.col_index[c.name]
        for ln in st.row_lines:
            if trim(ln.cells[j]) != "":
                raise Malformed(
                    f"value {trim(ln.cells[j])!r} in the computed column {c.name!r} (§9.17)"
                )

    for ln in st.lines:
        if ln.kind == "declaration":
            parse_declaration(st, ln)

    validate(st)
    return st


def strip_inline_annotation(body):
    """§4.1.10 -- an inline annotation is WSP followed by `#` to end of line,
    on a declaration line only.  `g := sum(v)# note` has no WSP before the `#`
    and is a malformed declaration."""
    in_str = False
    for i, ch in enumerate(body):
        if ch == '"':
            in_str = not in_str
        elif ch == "#" and not in_str and i > 0 and body[i - 1] in WSP:
            return body[:i]
    return body


def parse_declaration(st, ln):
    s = strip_inline_annotation(ln.body)
    s = trim(s)
    if ":=" not in s:
        # §9.19 -- none of annotation, table line, declaration, or blank.
        raise Malformed(
            f"line is not an annotation, table line, declaration or blank (§9.19): {ln.body[:60]!r}"
        )
    lhs, rhs = s.split(":=", 1)
    lhs, rhs = trim(lhs), trim(rhs)
    if lhs == "" or rhs == "":
        raise Malformed(f"malformed declaration (§9.12): {ln.body[:60]!r}")
    if not is_ident(lhs):
        raise Malformed(f"malformed declaration (§9.12): {lhs!r} is not an ident (§4.1.9)")

    if lhs == "key":
        if st.key is not None:
            raise Malformed("duplicate key declaration (§9.4)")
        # §4.1.11 -- `key := col` is the sole bare form.
        if not is_ident(rhs):
            raise Malformed("malformed declaration (§9.12): key takes a bare column name")
        st.key = nfc(rhs)
        return

    if lhs == "order":
        if st.order is not None:
            raise Malformed("duplicate order declaration (§9.4)")
        # §4.1.11 -- §6 defines exactly two order states; a third spelling is
        # refused rather than degraded into the second.
        m = re.match(r"^by\(([ \t]*)([^()]*?)([ \t]*)\)$", rhs)
        if not m or not is_ident(m.group(2)):
            raise Malformed(
                "malformed declaration (§9.12): unrecognised order construct "
                f"{rhs!r}; §6 defines only `order := by(c)` or the line omitted"
            )
        st.order = nfc(m.group(2))
        return

    name = check_identifier(lhs, "aggregate")
    if any(name == n for n, _ in st.aggregates):
        raise Malformed(f"duplicate aggregate name {name!r} (§9.3)")
    # §4.1.11 -- a non-`key` name with no function is malformed.
    if "(" not in rhs:
        raise Malformed(f"malformed declaration (§9.12): {ln.body[:60]!r} has no function")
    node = parse_formula(rhs, f"aggregate {name}")
    if node[0] != "agg":
        raise Malformed(
            f"malformed declaration (§9.12): {ln.body[:60]!r} is not an aggregate over a column"
        )
    for sub in walk(node):
        if sub[0] == "at":
            raise Malformed(
                f"malformed declaration (§9.12): @{sub[1]} has no current row in a "
                "table-level aggregate"
            )
    st.aggregates.append((name, node))


def validate(st):
    names = set(st.col_index)

    if st.key is not None:
        if st.key not in names:
            raise Malformed(f"key := {st.key} names no column")
        if st.columns[st.col_index[st.key]].computed:
            raise Malformed(f"key := {st.key} is a computed column")
        # §9.16 -- a value of the key column is an identifier.
        ki = st.col_index[st.key]
        seen = {}
        for ln in st.row_lines:
            v = check_identifier(trim(ln.cells[ki]), "row key")
            if v in seen:
                raise Malformed(f"duplicate key {v!r} (§9.5)")
            seen[v] = True

    # §9.9 -- a row-relative operator with no declared order
    if st.order is None:
        for c in st.columns:
            if c.computed and any(s[0] == "rowrel" for s in walk(c.formula)):
                raise Malformed("row-relative operator requires a declared row order (§9.9)")

    # §9.10 -- the order column
    if st.order is not None:
        if st.order not in names:
            raise Malformed(f"order := by({st.order}) names no column (§9.10)")
        if st.columns[st.col_index[st.order]].computed:
            raise Malformed(f"order := by({st.order}) is a computed column (§9.10)")
        if st.key is None:
            raise Malformed("order requires a declared key (§6, §9.10)")
        oi = st.col_index[st.order]
        kinds = {order_kind(trim(ln.cells[oi]), st.order) for ln in st.row_lines}
        if len(kinds) > 1:
            raise Malformed(
                "order := by({}) mixes types: {} (§9.10)".format(st.order, ", ".join(sorted(kinds)))
            )

    # §7/§8 -- a lookup path is literal, and confined to the repository.  The
    # lexical half of that is static; the containment half needs the base and
    # happens in Evaluator.
    for c in st.columns:
        if not c.computed:
            continue
        for sub in walk(c.formula):
            if sub[0] == "lookup" and os.path.isabs(sub[1]):
                raise Malformed(
                    f"lookup() target {sub[1]!r} is absolute; §7 confines it to the repository"
                )


def order_kind(s, col):
    if s == "":
        return "blank"
    if s.lower() in NONFINITE:
        raise Malformed(f"order := by({col}) holds the non-finite spelling {s!r} (§9.10)")
    if NUMBER_RE.match(s):
        return "number"
    if DATE_RE.match(s):
        return "date"
    return "text"


def parse(text):
    """Recognition; the same algorithm evaluate() runs (§9)."""
    return structure(text)


# --------------------------------------------------------------------------
# render / canon / set_cell
# --------------------------------------------------------------------------


def render(st):
    return "".join(ln.text() for ln in st.lines)


def canon_align(cell):
    s = trim(cell)
    left = s.startswith(":")
    right = s.endswith(":") and s != ":"
    return (":" if left else "-") + "-" + (":" if right else "-")


def canon(text):
    """§10.  Single-space delimiters, no alignment padding.

    §4.1.1: canon terminates every table line it emits and leaves annotations
    and declarations byte-verbatim.  §3/§10: the canonical form is LF -- read
    here as normalising every terminator, since a "canonical form" with two
    line endings in it is not canonical.  See the findings: the two sentences
    do not agree and no fixture separates them.
    """
    st = structure(text)
    for ln in st.lines:
        if ln.cells is None:
            ln.term = "\n" if ln.term else ln.term
            continue
        if ln.kind == "align":
            cells = [canon_align(c) for c in ln.cells]
        else:
            cells = [trim(c) for c in ln.cells]
        ln.cells = [" " + c + " " for c in cells]
        ln.head = ""
        ln.tail = ""
        ln.term = "\n"
    return render(st)


def set_cell(st, row_key, column, value):
    col = nfc(str(column))
    if col not in st.col_index:
        raise Malformed(f"no column named {column!r}")
    if st.columns[st.col_index[col]].computed:
        raise Malformed(f"cannot write a value into the computed column {column!r} (§5)")
    if st.key is None:
        raise Malformed("cannot address a row: no key is declared")
    ki = st.col_index[st.key]
    want = nfc(str(row_key))
    for ln in st.row_lines:
        if nfc(trim(ln.cells[ki])) == want:
            ln.cells[st.col_index[col]] = f" {value} "
            return st
    raise Malformed(f"no row with key {row_key!r}")


# --------------------------------------------------------------------------
# evaluation
# --------------------------------------------------------------------------


def sort_key_for(kind, s, key):
    """§6: the tuple (typed value of c, key), never a string concatenation.
    §4.1.7: dates compare as the integer tuple (y, m, d), never as strings.
    §4.1.8: text compares by Unicode code point over the NFC-normalised,
    trimmed value; locale collation is refused."""
    if kind == "number":
        return (float(s), key)
    if kind == "date":
        sep = "-" if "-" in s else "/"
        y, m, d = s.split(sep)
        return ((int(y), int(m), int(d)), key)
    if kind == "blank":
        return ("", key)
    return (nfc(s), key)


class Ctx:
    """Shared across one evaluation, including artifacts reached by lookup."""

    def __init__(self, root):
        self.root = root
        self.arts = {}  # abspath -> Evaluator
        self.stack = set()  # (abspath, column) currently being computed


class Evaluator:
    def __init__(self, st, base, ctx, path=None):
        self.st = st
        self.base = base
        self.ctx = ctx
        self.path = path or "<input>"
        self.n = len(st.row_lines)
        self.cache = {}
        self.stack = []

        if st.order is not None and self.n:
            oi = st.col_index[st.order]
            ki = st.col_index[st.key]
            kinds = {order_kind(trim(ln.cells[oi]), st.order) for ln in st.row_lines}
            kind = kinds.pop()
            dec = []
            for i, ln in enumerate(st.row_lines):
                dec.append(
                    (
                        sort_key_for(kind, trim(ln.cells[oi]), nfc(trim(ln.cells[ki]))),
                        i,
                    )
                )
            dec.sort(key=lambda t: t[0])
            self.perm = [i for _, i in dec]
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

    def raw_text(self, name, p):
        """Trimmed source text of a cell, for key comparison across a lookup."""
        if name not in self.st.col_index:
            return None
        col = self.st.columns[self.st.col_index[name]]
        if not col.computed:
            i = self.perm[p]
            return trim(self.st.row_lines[i].cells[self.st.col_index[name]])
        return as_text(self.column(name)[p])

    def ref_value(self, name, p):
        """A bare column reference used as an arithmetic operand (§8)."""
        vals = self.column(name)
        if vals is None:
            return Ref(name)
        v = vals[p]
        if isinstance(v, Ref):
            return v
        if v is BLANK or isinstance(v, TextVal):
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
            # §7: "@c means *this row's* value of c" -- compared for equality,
            # never coerced, or no text column could be grouped on.
            vals = self.column(node[1])
            return Ref(node[1]) if vals is None else vals[p]
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
        if t == "rowrel":
            return self.rowrel(node[1], node[2], p)
        if t == "agg":
            return self.aggregate(node[1], node[2], node[3], p)
        if t == "lookup":
            return self.lookup(node[1], node[2], node[3], p)
        raise Malformed(f"unevaluable expression node {node!r}")

    # -- lookup (§7, and §8's single permitted read) ----------------------

    def resolve(self, path):
        """Absolute path of a lookup target, refusing an escape from the
        repository root (§7: "confined to the repository")."""
        if self.base is None:
            return None
        target = os.path.normpath(os.path.join(self.base, path))
        rel = os.path.relpath(target, self.ctx.root)
        if rel == ".." or rel.startswith(".." + os.sep) or os.path.isabs(path):
            raise Malformed(f"lookup() target {path!r} escapes the repository root (§7)")
        return target

    def artifact(self, target):
        ev = self.ctx.arts.get(target)
        if ev is not None:
            return ev
        try:
            with open(target, encoding="utf-8", newline="") as fh:
                text = fh.read()
        except UnicodeDecodeError as ex:
            raise Malformed(
                f"lookup target {target} is not well-formed UTF-8 (§9.14): {ex}"
            ) from None
        # A refusal in the target is a refusal of the referring artifact:
        # parse/lookup-target-duplicate-keys.  Not stated in the spec.
        tst = structure(text)
        ev = Evaluator(tst, os.path.dirname(target), self.ctx, target)
        self.ctx.arts[target] = ev
        return ev

    def lookup(self, path, keycol, wantcol, p):
        kt = self.raw_text(keycol, p)
        if kt is None:
            return Ref(keycol)
        absent = Ref(f"{path}[{kt}]")
        target = self.resolve(path)
        if target is None or not os.path.isfile(target):
            return absent
        tev = self.artifact(target)
        tst = tev.st
        if tst.key is None:
            return absent
        ki = tst.col_index[tst.key]
        hit = None
        for q, i in enumerate(tev.perm):
            if nfc(trim(tst.row_lines[i].cells[ki])) == nfc(kt):
                hit = q
                break
        if hit is None:
            return absent
        if wantcol not in tst.col_index:
            return Ref(wantcol)
        guard = (target, wantcol)
        if guard in self.ctx.stack:
            # §8 requires the evaluator to terminate; a lookup cycle is not a
            # refusal (parse/lookup-cycle accepts one).
            return Ref(wantcol)
        self.ctx.stack.add(guard)
        try:
            return tev.column(wantcol)[hit]
        finally:
            self.ctx.stack.discard(guard)

    # -- aggregates ------------------------------------------------------

    def numeric_column(self, name):
        vals = self.column(name)
        if vals is None:
            return None
        out = []
        for v in vals:
            if isinstance(v, Ref) or v is BLANK:
                out.append(v)
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
            if a is BLANK or b is BLANK:
                return Ref(name)
            return a - b
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


def evaluate(text, base=None):
    """`base` is the directory the artifact lives in, needed only to resolve
    §7's lookup paths.  Without it every lookup is unresolved."""
    st = structure(text)
    root = os.path.abspath(base) if base is not None else None
    ctx = Ctx(root)
    ev = Evaluator(st, root, ctx)

    # cases/README.md: a `rowrel` case asserts one cell "in the *derived*
    # order", so the sequence is the derived order, not file order.
    rows = []
    for p, i in enumerate(ev.perm):
        ln = st.row_lines[i]
        row = {}
        for c in st.columns:
            if c.computed:
                row[c.name] = display(ev.column(c.name)[p])
            else:
                row[c.name] = trim(ln.cells[st.col_index[c.name]])
        rows.append(row)

    aggs = {}
    for name, node in st.aggregates:
        aggs[name] = display(ev.eval(node, 0))
    return rows, aggs
