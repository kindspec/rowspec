"""rowspec — a second, independent implementation, written from SPEC.md.

Entry points: parse, structure, evaluate, render, canon, set_cell, Malformed.
Standard library only.  Every non-obvious decision cites the clause it came
from; where the prose did not determine the answer the comment says so.
"""

import math
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
#
# §8 and §4.2 rule 10: the format has exactly two kinds of value, a number and
# an error.  BLANK and TextVal are not values of the format -- they are what a
# *cell* holds before §8 decides what it means as an operand, and neither ever
# reaches a computed cell except through the blank test of rule 10.
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


# §8: exactly four shapes and an implementation emits no fifth.  Two of them
# are spelled as a well-formed `ident` and so collide with a broken reference
# to a column of that name; §4.2 rule 9 accepts the collision, because both
# readings are errors and no computed value branches on which it is.
REF_DIV0 = Ref("/0")
REF_CYCLE = Ref("cycle")
REF_OVERFLOW = Ref("overflow")


def display(v):
    if isinstance(v, Ref):
        return f"#REF!({v.name})"
    if v is BLANK:
        return ""
    if isinstance(v, TextVal):
        return v.s
    return v


def fin(x):
    """§4.2 rule 2: an operation whose IEEE result is an infinity does not
    store one -- it is `#REF!(overflow)`.  Applied at every point a binary64
    value is produced, because `100...0 * 100...0` overflows in the operator
    while `1e200` is not even a number under §4.1.6."""
    if isinstance(x, float) and (x == math.inf or x == -math.inf):
        return REF_OVERFLOW
    return x


def accumulate(nums):
    """§8: an aggregate whose result is not finite is `#REF!(overflow)` --
    stated separately from §4.2 rule 2 because a `sum` of large but finite
    cells overflows without any single operation doing so.  The host
    accumulator (`math.fsum`) refuses to *produce* the infinity and raises
    instead, and §8's evaluator is total: the escape must become the value
    `#REF!(overflow)`, not a traceback."""
    try:
        return fin(math.fsum(nums))
    except OverflowError:
        return REF_OVERFLOW


# --------------------------------------------------------------------------
# §4.1 lexical layer
# --------------------------------------------------------------------------

WSP = " \t"

# §4.1.6: number = [ "-" ] 1*DIGIT [ "." 1*DIGIT ]; DIGIT is U+0030-U+0039 and
# nothing else.  A leading "+", an exponent, ".5", "5." and any digit grouping
# are refused and are therefore text.
NUMBER_RE = re.compile(r"^-?[0-9]+(?:\.[0-9]+)?$")

# §4.2: literal = 1*DIGIT [ "." 1*DIGIT ] -- unsigned (rule 7).
LITERAL_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")

ASCII_INT_RE = re.compile(r"^[0-9]+$")

# §4.1.7: 1*4DIGIT sep 1*2DIGIT sep 1*2DIGIT, both separators the same.
DATE_RE = re.compile(r"^[0-9]{1,4}([-/])[0-9]{1,2}\1[0-9]{1,2}$")

# §4.1.5: align-cell = [ ":" ] 1*"-" [ ":" ]
ALIGN_CELL_RE = re.compile(r"^:?-+:?$")

# §9.10: non-finite spellings, refused in an order column in any case.
NONFINITE = {"inf", "+inf", "-inf", "infinity", "+infinity", "-infinity", "nan", "+nan", "-nan"}

CONFLICT_PREFIXES = ("<" * 7, "=" * 7, ">" * 7, "|" * 7)

# §4.2: matched case-sensitively, and recognised only immediately before "(".
AGG_FUNCS = ("sum", "count", "min", "max", "avg")
ROWREL_FUNCS = ("cumulative", "prior", "delta")

# §9.23: an `expr` nesting parentheses more than 64 deep.  A `cond`'s
# parenthesis counts toward it exactly as a bare one does (§4.2 rule 10).
MAX_DEPTH = 64


def nfc(s):
    return unicodedata.normalize("NFC", s)


def is_ident_char(ch):
    """§4.1.9: ident = 1*( LETTER / MARK / NUM / "_" ).  An allowlist, so the
    answer for a character nobody has thought of yet is `refused`.  `-` and `.`
    are NOT in it (§4.1.9's second [CHOICE]); `Cf` falls out by construction,
    which is what §3 requires."""
    return ch == "_" or unicodedata.category(ch)[0] in ("L", "M", "N")


def is_ident(name):
    return bool(name) and all(is_ident_char(ch) for ch in name)


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


def unescape(s):
    """§4.1.3: the reader unescapes `\\|` in each cell of a table line.  A
    backslash not followed by `|` is a literal backslash."""
    return s.replace("\\|", "|") if "\\|" in s else s


def escape(s):
    """§4.1.3: a writer escapes every literal `|` it emits INTO a table line.
    Scoped to the table line: a declaration line is never unescaped, so it is
    never escaped either."""
    return s.replace("|", "\\|")


def cell_value(raw):
    """The value of a cell of a table line: trimmed, then unescaped."""
    return unescape(trim(raw))


def coerce_cell(raw):
    s = cell_value(raw)
    if s == "":
        return BLANK
    if NUMBER_RE.match(s):
        return fin(float(s))
    return TextVal(s)


# --------------------------------------------------------------------------
# §4.2 expression grammar — tokens
# --------------------------------------------------------------------------

TWO_CHAR_OPS = ("<=", ">=", "<>")
ONE_CHAR_OPS = "+-*/(),=@<>"
ORDER_OPS = ("<", "<=", ">", ">=")
EQ_OPS = ("=", "<>")


class Tok:
    __slots__ = ("kind", "text", "ws")

    def __init__(self, kind, text, ws):
        self.kind = kind  # "word" | "op" | "str"
        self.text = text
        self.ws = ws  # was this token preceded by WSP?

    def __repr__(self):
        return f"{self.kind}:{self.text!r}{'*' if self.ws else ''}"


def lex(src, ctx):
    """§4.2 rule 7: tokenisation is **maximal munch over `ident`**, and it
    happens BEFORE anything is classified as a literal.  `1000_2999` is one
    token, never `1000` followed by `_2999`; `1e3` and `0x10` are idents, not
    malformed numbers.  Only a token that is *entirely* `1*DIGIT [ "." 1*DIGIT ]`
    is ambiguous, and rule 7's position rule resolves that one.

    The decimal point is the one place munch must reach past `ident`: `.` is
    not an ident character, so an all-ASCII-digit run followed by `.` and a
    digit continues as one token.  §4.2 does not say this in so many words --
    it says `ident` is a strict superset of `literal`, which is true of the
    integer spelling only.  Reported as an under-determination."""
    toks = []
    i, n = 0, len(src)
    ws = False
    while i < n:
        ch = src[i]
        if ch in WSP:
            ws = True
            i += 1
            continue
        if ch == '"':
            # §4.2 rule 6: a double-quoted run that may not contain `"`, and
            # there is no escape inside it.
            j = src.find('"', i + 1)
            if j < 0:
                raise Malformed(f"{ctx}: unterminated string literal (§4.2 rule 6)")
            toks.append(Tok("str", src[i + 1 : j], ws))
            i = j + 1
        elif is_ident_char(ch):
            j = i
            while j < n and is_ident_char(src[j]):
                j += 1
            word = src[i:j]
            if (
                ASCII_INT_RE.match(word)
                and j + 1 < n
                and src[j] == "."
                and "0" <= src[j + 1] <= "9"
            ):
                k = j + 1
                while k < n and is_ident_char(src[k]):
                    k += 1
                word, j = src[i:k], k
            toks.append(Tok("word", word, ws))
            i = j
        elif src[i : i + 2] in TWO_CHAR_OPS:
            toks.append(Tok("op", src[i : i + 2], ws))
            i += 2
        elif ch in ONE_CHAR_OPS:
            toks.append(Tok("op", ch, ws))
            i += 1
        else:
            # §4.2 rule 1: the rule is that `expr` is exactly what the ABNF
            # generates, so `^`, `%`, `&`, `~`, `!` and every other operator
            # character refuse the formula without being listed.
            raise Malformed(f"{ctx}: {ch!r} is not a character of §4.2's grammar (§9.20)")
        ws = False
    return toks


# --------------------------------------------------------------------------
# §4.2 expression grammar — parser
# --------------------------------------------------------------------------


class P:
    def __init__(self, toks, ctx):
        self.t = toks
        self.i = 0
        self.ctx = ctx
        self.depth = 0

    def peek(self, k=0):
        j = self.i + k
        return self.t[j] if j < len(self.t) else None

    def take(self):
        tok = self.peek()
        self.i += 1
        return tok

    def at_end(self):
        return self.i >= len(self.t)

    def is_op(self, text, k=0):
        tok = self.peek(k)
        return tok is not None and tok.kind == "op" and tok.text == text

    def eat_op(self, text):
        if not self.is_op(text):
            self.fail(f"expected {text!r}")
        self.i += 1

    def fail(self, msg="is not generated by §4.2's `formula`"):
        raise Malformed(f"{self.ctx}: {msg} (§9.20)")

    def enter(self):
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise Malformed(f"{self.ctx}: parentheses nested more than {MAX_DEPTH} deep (§9.23)")

    def leave(self):
        self.depth -= 1


def parse_expr(p):
    """expr = term *( *WSP ( "+" / "-" ) *WSP term ) -- left-associative."""
    node = parse_term(p)
    while p.is_op("+") or p.is_op("-"):
        op = p.take().text
        node = ("bin", op, node, parse_term(p))
    return node


def parse_term(p):
    node = parse_factor(p)
    while p.is_op("*") or p.is_op("/"):
        op = p.take().text
        node = ("bin", op, node, parse_factor(p))
    return node


def parse_factor(p):
    """factor = [ "-" *WSP ] primary.  The bracket is zero-or-one and `-a` is
    not a `primary`, so `--a` and `- -a` are refused (§4.2 rule 7).  There is
    no unary `+`: `factor` does not generate one."""
    if p.is_op("-"):
        p.take()
        return ("neg", parse_primary(p))
    return parse_primary(p)


def parse_primary(p):
    """primary = literal / cond / ident / "(" *WSP expr *WSP ")"."""
    tok = p.peek()
    if tok is None:
        p.fail("expression ends where an operand was expected")
    if tok.kind == "op" and tok.text == "(":
        p.take()
        p.enter()
        node = parse_expr(p)
        p.eat_op(")")
        p.leave()
        return node
    if tok.kind == "word":
        # §4.2 rule 4: `if` is recognised ONLY immediately before "(", with no
        # WSP between the two.  Otherwise it is a column named `if`.
        if tok.text == "if" and p.is_op("(", 1) and not p.peek(1).ws:
            return parse_cond(p)
        p.take()
        # §4.2 rule 7: operand position tries `literal` first, so a token
        # matching `literal` is a number and never the column of that name.
        if LITERAL_RE.match(tok.text):
            return ("lit", fin(float(tok.text)))
        if is_ident(tok.text):
            return ("col", nfc(tok.text))
        p.fail(f"{tok.text!r} is neither a `literal` nor an `ident`")
    # A `string` outside a predicate, an `@` outside a predicate, and a `call`
    # composed into arithmetic all land here (§9.20; §4.2 rules 3, 5, 6).
    p.fail(f"{tok.text!r} cannot begin an operand")


def parse_cond(p):
    """cond = "if" "(" *WSP comparison *WSP "," *WSP expr *WSP "," *WSP expr
    *WSP ")" (§4.2 rule 10).  Its parenthesis counts toward §9.23 exactly as a
    bare one does: the recursion is the same recursion."""
    p.take()  # if
    p.take()  # (
    p.enter()
    cmp_node = parse_comparison(p)
    p.eat_op(",")
    a = parse_expr(p)
    p.eat_op(",")
    b = parse_expr(p)
    p.eat_op(")")
    p.leave()
    return ("if", cmp_node, a, b)


def parse_signed(p):
    """signed = [ "-" *WSP ] literal -- rule 10: a bound may be negative."""
    sign = 1.0
    if p.is_op("-"):
        p.take()
        sign = -1.0
    tok = p.peek()
    if tok is None or tok.kind != "word" or not LITERAL_RE.match(tok.text):
        return None
    p.take()
    return sign * float(tok.text)


def parse_comparison(p):
    """comparison = ident *WSP ( order-op *WSP order-rhs / eq-op *WSP eq-rhs ).

    The left-hand side is a NAME position (rule 7): it admits `ident` and has
    no literal alternative, so `if(123 > 0, a, b)` names the column `123`.
    """
    tok = p.peek()
    if tok is None or tok.kind != "word" or not is_ident(tok.text):
        p.fail("the left-hand side of a comparison must be an `ident`")
    p.take()
    lhs = nfc(tok.text)
    op_tok = p.peek()
    if op_tok is None or op_tok.kind != "op" or op_tok.text not in ORDER_OPS + EQ_OPS:
        p.fail("a comparison needs one of `<` `<=` `>` `>=` `=` `<>`")
    p.take()
    op = op_tok.text
    if op in ORDER_OPS:
        # order-rhs = signed / ident.  Operand position: `literal` first.
        mark = p.i
        val = parse_signed(p)
        if val is not None:
            return ("cmp", op, lhs, "num", fin(val))
        p.i = mark
        rtok = p.peek()
        if rtok is not None and rtok.kind == "word" and is_ident(rtok.text):
            p.take()
            return ("cmp", op, lhs, "col", nfc(rtok.text))
        p.fail("the right-hand side of an ordering comparison must be a `signed` or an `ident`")
    # eq-rhs = string / signed.  No `ident` alternative -- §9.24.
    rtok = p.peek()
    if rtok is not None and rtok.kind == "str":
        p.take()
        return ("cmp", op, lhs, "str", nfc(rtok.text))
    mark = p.i
    val = parse_signed(p)
    if val is not None:
        return ("cmp", op, lhs, "num", fin(val))
    p.i = mark
    p.fail(
        "the right-hand side of `=` or `<>` must be a `string` or a `signed`; "
        "an `ident` there is refused (§9.24)"
    )


def parse_predicate(p, allow_at):
    """predicate = equality *( 1*WSP "and" 1*WSP equality )
    equality  = ident *WSP "=" *WSP pred-rhs
    pred-rhs  = string / at-ref          ; at-ref: header cells only, rule 5

    Returns None when the token stream is not a predicate, so `formula`'s
    `call` alternative can fall through to `expr` rather than commit."""
    preds = []
    while True:
        tok = p.peek()
        if tok is None or tok.kind != "word" or not is_ident(tok.text) or not tok.ws:
            return None
        p.take()
        lhs = nfc(tok.text)
        if not p.is_op("="):
            return None
        p.take()
        rtok = p.peek()
        if rtok is not None and rtok.kind == "str":
            p.take()
            preds.append((lhs, "str", nfc(rtok.text)))
        elif allow_at and rtok is not None and rtok.kind == "op" and rtok.text == "@":
            p.take()
            ntok = p.peek()
            # at-ref = "@" ident, with no WSP between the two.
            if ntok is None or ntok.kind != "word" or not is_ident(ntok.text) or ntok.ws:
                return None
            p.take()
            preds.append((lhs, "at", nfc(ntok.text)))
        else:
            return None
        nxt = p.peek()
        if nxt is not None and nxt.kind == "word" and nxt.text == "and" and nxt.ws:
            p.take()
            # §4.2 rule 8: 1*WSP on BOTH sides of `and`.
            if p.peek() is None or not p.peek().ws:
                return None
            continue
        return tuple(preds)


def parse_call(toks, ctx):
    """call = rowrel-call / group-call.  Returns None -- not a refusal -- when
    the stream is not a call, so `formula = call / expr` can try `expr` next.

    §4.2 rule 3: a call is the whole formula or nothing; it never appears as a
    `primary` and `expr` has no call alternative.  That is why this is a
    separate top-level recogniser rather than a case in `parse_primary`."""
    if len(toks) < 4 or toks[0].kind != "word":
        return None
    name = toks[0].text
    # §4.2 rule 4: recognised only immediately before "(", case-sensitively.
    if not (toks[1].kind == "op" and toks[1].text == "(" and not toks[1].ws):
        return None
    if name in ROWREL_FUNCS:
        # rowrel-fn "(" *WSP ident *WSP ")"
        if len(toks) != 4:
            return None
        arg, close = toks[2], toks[3]
        if arg.kind != "word" or not is_ident(arg.text):
            return None
        if close.kind != "op" or close.text != ")":
            return None
        return ("rowrel", name, nfc(arg.text))
    if name in AGG_FUNCS:
        # group-call = agg-fn "(" *WSP ident 1*WSP "where" 1*WSP predicate *WSP ")"
        # The `where` is REQUIRED in a header cell; only §4.1's `arg`, on a
        # declaration line, makes it optional.
        p = P(toks, ctx)
        p.i = 2
        arg = p.peek()
        if arg is None or arg.kind != "word" or not is_ident(arg.text):
            return None
        p.take()
        w = p.peek()
        if w is None or w.kind != "word" or w.text != "where" or not w.ws:
            return None
        p.take()
        preds = parse_predicate(p, allow_at=True)
        if preds is None or not p.is_op(")"):
            return None
        p.take()
        if not p.at_end():
            return None
        return ("agg", name, nfc(arg.text), preds)
    return None


def parse_formula(src, ctx):
    """formula = call / expr -- a header cell's right-hand side, ENTIRE.

    §4.2: "Recognition is whole-cell."  There is no partial parse and no
    fallback to text."""
    toks = lex(src, ctx)
    if not toks:
        raise Malformed(f"{ctx}: empty formula (§9.20)")
    node = parse_call(toks, ctx)
    if node is not None:
        return node
    p = P(toks, ctx)
    node = parse_expr(p)
    if not p.at_end():
        p.fail(f"trailing {p.peek().text!r}")
    return node


# --------------------------------------------------------------------------
# walking a parsed formula
# --------------------------------------------------------------------------


def iter_nodes(node):
    yield node
    t = node[0]
    if t == "bin":
        yield from iter_nodes(node[2])
        yield from iter_nodes(node[3])
    elif t == "neg":
        yield from iter_nodes(node[1])
    elif t == "if":
        yield node[1]
        yield from iter_nodes(node[2])
        yield from iter_nodes(node[3])


def names_in(node):
    """Every column name a formula references, in source order.

    §4.2 rule 9: dependency and cycle analysis is over the whole formula, both
    branches of a `cond` included, and is not affected by which branch a row
    selects."""
    out = []
    for nd in iter_nodes(node):
        t = nd[0]
        if t == "col":
            out.append(nd[1])
        elif t == "rowrel":
            out.append(nd[2])
        elif t == "agg":
            out.append(nd[2])
            for lhs, kind, val in nd[3]:
                out.append(lhs)
                if kind == "at":
                    out.append(val)
        elif t == "cmp":
            out.append(nd[2])
            if nd[3] == "col":
                out.append(nd[4])
    return out


def stored_only_names(node):
    """The names §9.22 requires to be STORED columns, with a reason each.

    §4.2 rule 5: both idents of a `where` equality.  §4.2 rule 10: the
    left-hand ident of an `=`/`<>` comparison whose right-hand side is a
    `string`.  A *numeric* right-hand side carries no such restriction, and
    neither does an ordering comparison."""
    out = []
    for nd in iter_nodes(node):
        if nd[0] == "agg":
            for lhs, kind, val in nd[3]:
                out.append((lhs, "the left-hand side of a `where` equality"))
                if kind == "at":
                    out.append((val, "an `@` reference in a `where` predicate"))
        elif nd[0] == "cmp" and nd[1] in EQ_OPS and nd[3] == "str":
            out.append((nd[2], "the left-hand side of a string `=`/`<>` comparison inside `if`"))
    return out


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
    """LF and CRLF are both `eol` (§4.1.1).  A lone CR is refused (§9.15)."""
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


def split_table_line(body):
    """§4.1.3: a reader splits a TABLE LINE on unescaped pipes.

        table-line = *WSP "|" 1*( cell "|" ) *WSP
        cell       = *( escaped / ( char - "|" ) )
        escaped    = "\\" "|"                      ; the sole escape

    Returns (head, raw_cells, tail) or None when the line is not a table line
    -- in particular when it lacks its closing `|` (§9.18).  Cells are kept in
    their escaped source spelling so that `render` is byte-exact."""
    n = len(body)
    i = 0
    while i < n and body[i] in WSP:
        i += 1
    if i >= n or body[i] != "|":
        return None
    head = body[:i]
    i += 1
    cells = []
    cur = []
    while True:
        if i >= n:
            return None  # no closing pipe
        ch = body[i]
        if ch == "\\" and i + 1 < n and body[i + 1] == "|":
            cur.append("\\|")
            i += 2
        elif ch == "|":
            cells.append("".join(cur))
            cur = []
            i += 1
            j = i
            while j < n and body[j] in WSP:
                j += 1
            if j >= n:
                return head, cells, body[i:]
        else:
            cur.append(ch)
            i += 1


def classify(line):
    """§4.1: the alternatives of `line` are tried in the order written and the
    first that matches decides.  `conflict` precedes `table-line` because
    `|||||||` is itself a well-formed seven-cell table line; `annotation`
    precedes it because `# | r_9999 | ghost | 100 |` must stay inert."""
    b = line.body
    if b[:7] in CONFLICT_PREFIXES:
        return "conflict"
    stripped = b.lstrip(WSP)
    if stripped.startswith("#"):
        return "annotation"
    if split_table_line(b) is not None:
        return "table"
    if stripped == "":
        return "blank"
    # `declaration` is provisional: a line that contains `:=` and does not
    # match `declaration` is §9.12, and one that matches no alternative at all
    # is §9.19.  parse_declaration decides which.
    return "declaration"


def is_align_row(cells):
    """§4.1.5.  A *data* row is alignment-style (§9.8) iff EVERY one of its
    cells matches `align-cell`; a single `---` beside ordinary values is data."""
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

    # §9.1 / §4.1.12 -- conflict markers anywhere, before any other
    # classification.
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
        ln.head, ln.cells, ln.tail = split_table_line(ln.body)

    # §9.21 -- a table shorter than two lines, or a second line that is not a
    # valid alignment row.  Never reinterpreted as a data row (§4).
    if end - start < 2:
        raise Malformed("table is shorter than two lines: no alignment row (§9.21)")
    header, align = st.lines[start], st.lines[start + 1]
    header.kind, align.kind = "header", "align"
    ncol = len(header.cells)
    if len(align.cells) != ncol:
        raise Malformed(f"alignment row has {len(align.cells)} fields, header has {ncol} (§9.7)")
    if not is_align_row(align.cells):
        raise Malformed(
            f"second table line is not a valid alignment row (§9.21): {align.body[:60]!r}"
        )

    # §5 -- header cells.  The split is at the cell's FIRST `=`; `=` is outside
    # `ident`, so the first one can only be the separator and every later one
    # belongs to a predicate or a comparison.
    seen = set()
    for c in header.cells:
        raw = cell_value(c)
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
                raise Malformed(f"column {name}: empty formula (§9.20)")
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
            if cell_value(ln.cells[j]) != "":
                raise Malformed(
                    f"value {cell_value(ln.cells[j])!r} in the computed column {c.name!r} (§9.17)"
                )

    for ln in st.lines:
        if ln.kind == "declaration":
            parse_declaration(st, ln)

    validate(st)
    return st


def strip_inline_annotation(body):
    """§4.1.10 -- an inline annotation is WSP followed by `#` to end of line,
    on a declaration line only.  `g := sum(v)# note` has no WSP before the `#`
    and is a malformed declaration.  The scan is string-aware because §4.2
    rule 6's `string` may contain both WSP and `#`, and the ABNF places the
    annotation after the whole `rhs`."""
    in_str = False
    for i, ch in enumerate(body):
        if ch == '"':
            in_str = not in_str
        elif ch == "#" and not in_str and i > 0 and body[i - 1] in WSP:
            return body[:i]
    return body


def parse_decl_rhs(src, ctx):
    """§4.1: rhs = ident "(" *WSP arg *WSP ")" / ident
             arg = ident [ 1*WSP "where" 1*WSP predicate ]

    Returns ("bare", name) or ("call", fname, arg, preds).  §4.2: the same
    `predicate`, with `at-ref` removed -- a table-level aggregate has no
    current row for `@` to refer to (rule 5)."""
    try:
        toks = lex(src, ctx)
    except Malformed as ex:
        # §9.20 is scoped to a header cell; a declaration line is §9.12.
        raise Malformed(f"malformed declaration (§9.12): {ex}") from None
    if not toks:
        raise Malformed(f"malformed declaration (§9.12): {ctx} has an empty right-hand side")
    if len(toks) == 1 and toks[0].kind == "word" and is_ident(toks[0].text):
        return ("bare", nfc(toks[0].text))
    if (
        len(toks) >= 4
        and toks[0].kind == "word"
        and is_ident(toks[0].text)
        and toks[1].kind == "op"
        and toks[1].text == "("
        and not toks[1].ws
    ):
        p = P(toks, ctx)
        p.i = 2
        arg = p.peek()
        if arg is None or arg.kind != "word" or not is_ident(arg.text):
            raise Malformed(f"malformed declaration (§9.12): {ctx} takes a column name")
        p.take()
        preds = ()
        w = p.peek()
        if w is not None and w.kind == "word" and w.text == "where" and w.ws:
            p.take()
            preds = parse_predicate(p, allow_at=False)
            if preds is None:
                raise Malformed(
                    f"malformed declaration (§9.12): {ctx} has a `where` clause that is "
                    "not a `predicate` -- an `@` reference has no current row here "
                    "(§4.2 rule 5)"
                )
        if not p.is_op(")"):
            raise Malformed(f"malformed declaration (§9.12): {ctx} is not a closed `rhs`")
        p.take()
        if not p.at_end():
            raise Malformed(f"malformed declaration (§9.12): {ctx} has trailing tokens")
        return ("call", toks[0].text, nfc(arg.text), preds)
    raise Malformed(f"malformed declaration (§9.12): {ctx} does not match `rhs`")


def parse_declaration(st, ln):
    s = trim(strip_inline_annotation(ln.body))
    if ":=" not in s:
        # §9.18 and §9.19 both claim this line, and the document does not say
        # which. §9.19 is the classification rule of §4.1: the line matched no
        # alternative of `line`. §9.18 names the sub-case, "a table line that
        # does not match `table-line`, in particular one lacking its closing
        # `|`" -- but nothing distinguishes a *table* line that fails to match
        # from any other unmatched line except that it starts with `|`, so
        # that is the test used here. §9's own note makes the choice
        # unobservable: which refusal is reported is deliberately unspecified.
        if ln.body.lstrip(WSP).startswith("|"):
            raise Malformed(
                "table line does not match `table-line`, most likely a missing "
                f"closing `|` (§9.18): {ln.body[:60]!r}"
            )
        raise Malformed(
            f"line is not an annotation, table line, declaration or blank (§9.19): {ln.body[:60]!r}"
        )
    lhs, rhs = s.split(":=", 1)
    lhs, rhs = trim(lhs), trim(rhs)
    ctx = repr(ln.body[:60])
    if lhs == "" or rhs == "":
        raise Malformed(f"malformed declaration (§9.12): {ctx}")
    if not is_ident(lhs):
        raise Malformed(f"malformed declaration (§9.12): {lhs!r} is not an ident (§4.1.9)")

    if lhs == "key":
        if st.key is not None:
            raise Malformed("duplicate key declaration (§9.4)")
        form = parse_decl_rhs(rhs, ctx)
        # §4.1.11 -- `key := col` is the sole bare form.
        if form[0] != "bare":
            raise Malformed(
                f"malformed declaration (§9.12): key takes a bare column name, not {rhs!r}"
            )
        st.key = form[1]
        return

    if lhs == "order":
        if st.order is not None:
            raise Malformed("duplicate order declaration (§9.4)")
        # §4.1.11 -- §6 defines exactly two order states, `order := by(c)` and
        # the line omitted entirely; a third spelling is refused rather than
        # degraded into the second.
        form = parse_decl_rhs(rhs, ctx)
        if form[0] != "call" or form[1] != "by" or form[3]:
            raise Malformed(
                "malformed declaration (§9.12): unrecognised order construct "
                f"{rhs!r}; §6 defines only `order := by(c)` or the line omitted"
            )
        st.order = form[2]
        return

    name = check_identifier(lhs, "aggregate")
    if any(name == n for n, _ in st.aggregates):
        raise Malformed(f"duplicate aggregate name {name!r} (§9.3)")
    form = parse_decl_rhs(rhs, ctx)
    # §4.1.11 -- a non-`key` name with no function is malformed.
    if form[0] != "call":
        raise Malformed(f"malformed declaration (§9.12): {ctx} has no function")
    if form[1] not in AGG_FUNCS:
        # §7 "An unknown function is refused."  §9.11 names it.  A `rowrel-fn`
        # lands here too: §7 scopes those to a header cell.
        raise Malformed(f"unknown aggregate function {form[1]!r} (§9.11)")
    st.aggregates.append((name, ("agg", form[1], form[2], form[3])))


def validate(st):
    names = set(st.col_index)

    if st.key is not None:
        if st.key not in names:
            raise Malformed(f"key := {st.key} names no column")
        if st.columns[st.col_index[st.key]].computed:
            raise Malformed(f"key := {st.key} is a computed column")
        # §9.16 -- a value of the key column is an identifier.
        ki = st.col_index[st.key]
        seen = set()
        for ln in st.row_lines:
            v = check_identifier(cell_value(ln.cells[ki]), "row key")
            if v in seen:
                raise Malformed(f"duplicate key {v!r} (§9.5)")
            seen.add(v)

    formulas = [(c.name, c.formula) for c in st.columns if c.computed]
    formulas += [(n, node) for n, node in st.aggregates]

    # §9.9 -- a row-relative operator with no declared order
    if st.order is None:
        for _, node in formulas:
            if any(nd[0] == "rowrel" for nd in iter_nodes(node)):
                raise Malformed("row-relative operator requires a declared row order (§9.9)")

    # §9.22 -- an ident that must name a STORED column.  Semantic, so §9.20
    # cannot reach it: no grammar can tell a stored column from a computed one.
    for owner, node in formulas:
        for nm, where in stored_only_names(node):
            if nm in names and st.columns[st.col_index[nm]].computed:
                raise Malformed(f"{owner}: {where} names the computed column {nm!r} (§9.22)")

    # §9.10 -- the order column
    if st.order is not None:
        if st.order not in names:
            raise Malformed(f"order := by({st.order}) names no column (§9.10)")
        if st.columns[st.col_index[st.order]].computed:
            raise Malformed(f"order := by({st.order}) is a computed column (§9.10)")
        if st.key is None:
            raise Malformed("order requires a declared key (§6, §9.10)")
        oi = st.col_index[st.order]
        kinds = {order_kind(cell_value(ln.cells[oi]), st.order) for ln in st.row_lines}
        if len(kinds) > 1:
            raise Malformed(
                "order := by({}) mixes types: {} (§9.10)".format(st.order, ", ".join(sorted(kinds)))
            )


def order_kind(s, col):
    if s == "":
        return "blank"
    if s.lower() in NONFINITE:
        raise Malformed(f"order := by({col}) holds the non-finite spelling {s!r} (§9.10)")
    if NUMBER_RE.match(s):
        if fin(float(s)) is REF_OVERFLOW:
            raise Malformed(f"order := by({col}) holds a non-finite value {s!r} (§9.10)")
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
            # trim only: the cell keeps its escaped `\|` spelling, which is
            # what §4.1.3 requires a writer to emit into a table line.
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
        if nfc(cell_value(ln.cells[ki])) == want:
            # §4.1.3: a writer escapes every literal `|` it emits INTO a table
            # line, and that is the sole escape.
            ln.cells[st.col_index[col]] = " " + escape(str(value)) + " "
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


class Evaluator:
    def __init__(self, st):
        self.st = st
        self.n = len(st.row_lines)
        self.cache = {}

        if st.order is not None and self.n:
            oi = st.col_index[st.order]
            ki = st.col_index[st.key]
            kinds = {order_kind(cell_value(ln.cells[oi]), st.order) for ln in st.row_lines}
            kind = kinds.pop()
            dec = [
                (
                    sort_key_for(
                        kind,
                        cell_value(ln.cells[oi]),
                        nfc(cell_value(ln.cells[ki])),
                    ),
                    i,
                )
                for i, ln in enumerate(st.row_lines)
            ]
            dec.sort(key=lambda t: t[0])
            self.perm = [i for _, i in dec]
        else:
            self.perm = list(range(self.n))

        self.poisoned = self._cycles()

    # -- §4.2 rule 9: static dependency and cycle analysis ----------------

    def _cycles(self):
        """A cycle evaluates to `#REF!(cycle)`, in every column on the cycle
        and in every column whose formula depends, directly or transitively,
        on one.  The analysis is over the whole formula -- both branches of a
        `cond` included -- and is NOT affected by which branch a row selects,
        so it must be static: `| x = if(c > 0, 0, x) |` is `#REF!(cycle)` even
        in the rows where the cycle is never reached."""
        st = self.st
        deps = {}
        for c in st.columns:
            if c.computed:
                deps[c.name] = [n for n in names_in(c.formula) if n in st.col_index]
        # Transitive closure by fixpoint rather than by a recursive walk: a
        # recursive walk needs a provisional value on re-entry, and any
        # provisional value under-reports exactly on the cycles this is
        # looking for.
        reach = {}
        for _ in range(len(deps) + 1):
            changed = False
            for name in deps:
                acc = set()
                for d in deps[name]:
                    acc.add(d)
                    acc |= reach.get(d, set())
                if reach.get(name) != acc:
                    reach[name] = acc
                    changed = True
            if not changed:
                break
        on_cycle = {name for name in deps if name in reach.get(name, ())}
        return {name for name in deps if name in on_cycle or (reach.get(name, set()) & on_cycle)}

    # -- columns ---------------------------------------------------------

    def column(self, name):
        """Values of `name` for every row, indexed by DERIVED position."""
        if name in self.cache:
            return self.cache[name]
        if name not in self.st.col_index:
            return None
        col = self.st.columns[self.st.col_index[name]]
        idx = self.st.col_index[name]
        if col.computed and name in self.poisoned:
            vals = [REF_CYCLE] * self.n
        elif not col.computed:
            vals = [coerce_cell(self.st.row_lines[i].cells[idx]) for i in self.perm]
        else:
            missing = self.static_miss(col.formula)
            if missing is not None:
                # §4.2 rule 10: a name that does not resolve is `#REF!(name)`
                # in EVERY row, even where the branch naming it is not
                # selected.  Whether a name resolves is a property of the
                # header alone.
                vals = [Ref(missing)] * self.n
            else:
                vals = [self.eval(col.formula, p) for p in range(self.n)]
        self.cache[name] = vals
        return vals

    def static_miss(self, node):
        for nm in names_in(node):
            if nm not in self.st.col_index:
                return nm
        return None

    def stored_text(self, name, p):
        """A cell's value as TEXT: trimmed, unescaped, NFC (§4.2 rule 6).
        Only ever asked of a stored column -- §9.22 refuses the alternative."""
        i = self.perm[p]
        return nfc(cell_value(self.st.row_lines[i].cells[self.st.col_index[name]]))

    def operand(self, name, p):
        """A column reference used as a numeric operand (§8).  A blank cell is
        not zero and a value that will not coerce is `#REF!`, not a guess."""
        vals = self.column(name)
        if vals is None:
            return Ref(name)
        v = vals[p]
        if isinstance(v, Ref):
            return v
        if v is BLANK or isinstance(v, TextVal):
            return Ref(name)
        return fin(v)

    # -- expressions -----------------------------------------------------

    def eval(self, node, p):
        t = node[0]
        if t == "lit":
            return node[1]
        if t == "col":
            return self.operand(node[1], p)
        if t == "neg":
            v = self.eval(node[1], p)
            return v if isinstance(v, Ref) else fin(-v)
        if t == "bin":
            a = self.eval(node[2], p)
            if isinstance(a, Ref):
                return a
            b = self.eval(node[3], p)
            if isinstance(b, Ref):
                return b
            op = node[1]
            if op == "+":
                return fin(a + b)
            if op == "-":
                return fin(a - b)
            if op == "*":
                return fin(a * b)
            # §4.2 rule 2: `/` is real division, and division by zero is a
            # VALUE -- the divisor is data, so a refusal would make a file
            # valid today refused when one cell is edited to `0`.
            if b == 0:
                return REF_DIV0
            return fin(a / b)
        if t == "if":
            return self.eval_if(node, p)
        if t == "rowrel":
            return self.rowrel(node[1], node[2], p)
        if t == "agg":
            return self.aggregate(node[1], node[2], node[3], p)
        raise Malformed(f"unevaluable expression node {node!r}")

    # -- §4.2 rule 10: `if` ----------------------------------------------

    def eval_if(self, node, p):
        cond = self.condition(node[1], p)
        if isinstance(cond, Ref):
            return cond
        # Only the selected branch is evaluated.  An implementation that
        # evaluates both computes a different table.
        return self.eval(node[2] if cond else node[3], p)

    def condition(self, cmp_node, p):
        _, op, lhs, rkind, rval = cmp_node
        if op in ORDER_OPS:
            # `<`, `<=`, `>`, `>=` are numeric, ALWAYS.  An operand that is
            # not a number -- blank, text, or an error -- makes the whole
            # `cond` that error, exactly as it would in arithmetic.
            a = self.operand(lhs, p)
            if isinstance(a, Ref):
                return a
            b = rval if rkind == "num" else self.operand(rval, p)
            if isinstance(b, Ref):
                return b
            if op == "<":
                return a < b
            if op == "<=":
                return a <= b
            if op == ">":
                return a > b
            return a >= b
        # `=` and `<>` compare text or numbers, and the RIGHT-HAND SIDE's
        # spelling decides which.
        if rkind == "str":
            vals = self.column(lhs)
            if vals is None:
                return Ref(lhs)
            v = vals[p]
            if isinstance(v, Ref):
                # An error operand is an error under every operator, `=` and
                # `<>` included.  It is *not* treated as blank.
                return v
            # `if(x = "", a, b)` is the blank test: a blank cell's text is the
            # empty string, so the equality is true and it does not become
            # `#REF!(x)` the way `x + 1` does.
            got = self.stored_text(lhs, p)
            res = got == rval
        else:
            a = self.operand(lhs, p)
            if isinstance(a, Ref):
                return a
            if isinstance(rval, Ref):
                # A `signed` bound whose binary64 value is an infinity: the
                # bound itself is `#REF!(overflow)` (rule 2), and an error
                # operand is an error under every operator, `=` included.
                return rval
            res = a == rval
        return res if op == "=" else not res

    # -- §7 row-relative operators ---------------------------------------

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
                out.append(fin(v))
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
            return fin(a - b)
        total = 0.0
        for i in range(p + 1):
            v = vals[i]
            if isinstance(v, Ref):
                return v
            if v is BLANK:
                return Ref(name)
            total = total + v
        return fin(total)

    # -- §7 aggregates ---------------------------------------------------

    def matches(self, preds, cand, cur):
        """§4.2 rule 5's binding rule: the `@` references are bound once, to
        the row whose cell is being computed, and held FIXED while the
        aggregated column is scanned over every row.  Binding them to the
        candidate row makes every equality trivially true and turns every
        group aggregate into a grand total -- a plausible number in every cell
        and an error in none.

        Equality compares TEXT, never numbers (rule 6), so `where qty = "3"`
        matches a cell holding `3` and not one holding `3.0`.  Both idents are
        stored columns by §9.22, so there is no error case here."""
        for lhs, kind, val in preds:
            got = self.stored_text(lhs, cand)
            want = val if kind == "str" else self.stored_text(val, cur)
            if got != want:
                return False
        return True

    def aggregate(self, fn, name, preds, p):
        vals = self.column(name)
        if vals is None:
            return Ref(name)
        sel = [vals[q] for q in range(self.n) if self.matches(preds, q, p)]
        if fn == "count":
            # §7: `count` counts rows and never coerces.  It is poisoned by a
            # `#REF!` actually present in the column, because that is an error
            # value -- but not by a value that merely fails to parse as a
            # number, because `count` never uses it as an operand.
            for v in sel:
                if isinstance(v, Ref):
                    return v
            return float(len(sel))
        nums = []
        for v in sel:
            # §8: an aggregate over any column containing a `#REF!` is itself
            # `#REF!` -- it must not sum the values it can read.
            if isinstance(v, Ref):
                return v
            if v is BLANK:
                continue
            if isinstance(v, TextVal):
                return Ref(name)
            nums.append(v)
        if fn == "sum":
            return accumulate(nums) if nums else 0.0
        if not nums:
            return BLANK
        if fn == "min":
            return min(nums)
        if fn == "max":
            return max(nums)
        total = accumulate(nums)
        if isinstance(total, Ref):
            return total
        return fin(total / len(nums))


def evaluate(text):
    st = structure(text)
    ev = Evaluator(st)

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
                row[c.name] = cell_value(ln.cells[st.col_index[c.name]])
        rows.append(row)

    aggs = {}
    for name, node in st.aggregates:
        miss = ev.static_miss(node)
        aggs[name] = display(Ref(miss) if miss else ev.eval(node, 0))
    return rows, aggs
