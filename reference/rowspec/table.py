#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Row-relative computation WITHOUT coordinates.

The insight: `prev.` failed not because row-relative computation is wrong, but
because "the row above" is a PLACE. If the table declares what determines row
order, then "the previous row" is a NOMINAL relationship -- "the row with the
next-lower key" -- and is independent of physical position, insertion, and
merge order.

    order := by(date)     row-relative ops legal, order derived from DATA
    order := none         row-relative ops are a PARSE ERROR (default)
"""

import math
import operator
import re
import sys
import unicodedata


class Malformed(Exception):
    """A refusal. `refusal` is its SPEC §9 identifier. It is None for an error
    that is not one of §9's refusals -- a sidecar's own, or a misuse of
    `set_cell` -- and, for now, for CSV mode, whose conformance cases still
    assert on the message."""

    def __init__(self, message, *, refusal=None):
        super().__init__(message)
        self.refusal = refusal


CONFLICT = ("<<<<<<<", "=======", ">>>>>>>", "|||||||")
ROWREL = {"cumulative", "prior", "delta"}
INF = float("inf")
# §4.1: `WSP = SP / HTAB`, never the Unicode White_Space property. Every
# trim and every regex the grammar writes with WSP uses this, not `\s`.
WSP = " \t"
BLANK = object()  # "the preceding row exists and is blank" -- not None


class _Text(str):
    """A stored cell spelled like an error value, such as `#REF!(zz)`.

    An error is a computed value; a stored cell is a number or text (§4.1 rule
    6). Computed errors are strings too, so a stored cell that merely spells
    one is marked, and nothing that asks "is this an error?" mistakes it.
    """


def _is_ref(v):
    return isinstance(v, str) and v.startswith("#REF!") and not isinstance(v, _Text)


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
    # `structure` passes a line with its terminator, which is not WSP.
    body = line.rstrip("\r\n").strip(WSP)
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
    if not name:
        # §4.1: `ident = 1*( ... )`. A name of no characters has no bad
        # character for the loops below to find, and would key a column ''.
        raise Malformed(
            f"{what} is empty; §4.1.9 makes an identifier one or more letters, "
            f"marks, digits or underscores",
            refusal="bad-identifier",
        )
    for ch in name:
        if ch in _STRUCTURAL or (
            not (ch.isalnum() or unicodedata.category(ch).startswith("M"))
            and ch not in _IDENT_EXTRA
            and not ch.isspace()
        ):
            raise Malformed(
                f"{what} {name!r} contains {ch!r}, which is not permitted in an "
                f"identifier; §4.1.9 admits letters, marks, digits and underscore",
                refusal="bad-identifier",
            )
    for ch in name:
        if unicodedata.category(ch) == "Cf":
            raise Malformed(
                f"{what} {name!r} contains a Cf format character U+{ord(ch):04X}",
                refusal="bad-identifier",
            )
        if ch.isspace():
            raise Malformed(
                f"{what} {name!r} contains whitespace U+{ord(ch):04X}; two identifiers "
                f"must not render identically",
                refusal="bad-identifier",
            )


def _is_ident(name):
    """§4.1's `ident` as a test: one or more characters, each admitted by
    `_check_ident`."""
    try:
        _check_ident(name, "")
    except Malformed:
        return False
    return name != ""


_ANNOT = re.compile(r'"[^"]*"|[ \t]#')


def _strip_annotation(line):
    r"""Cut an inline annotation, skipping string literals (§4.1.10).

    `re.sub(r"\s+#.*$", ...)` cut at the first ` #` anywhere, so
    `g := sum(a where r = "x #y")` was truncated mid-string and the line was
    then refused as a malformed declaration -- a valid file rejected. §4.2
    rule 6's `string` may contain both WSP and `#`, and the ABNF says so by
    placing the annotation after the whole `rhs`.
    """
    for m in _ANNOT.finditer(line):
        if m.group().startswith('"'):
            continue  # a string literal: its contents are not a scan
        return line[: m.start()]
    return line


def split_lines(text, keepends=False):
    """Split on `eol = LF / CRLF` (§4.1) and nothing else.

    `str.splitlines()` also breaks on VT, FF, U+001C-U+001E, NEL, U+2028 and
    U+2029, each of which is a `char`, so it split one table line in two.
    A lone CR is refused before this is reached (§3)."""
    out = text.split("\n")
    last = out.pop()
    if keepends:
        out = [ln + "\n" for ln in out]
    else:
        out = [ln[:-1] if ln.endswith("\r") else ln for ln in out]
    if last:
        out.append(last)
    return out


def parse(text):
    if text.startswith("\ufeff"):
        # §9.26: a property of the bytes, decided before any line is classified.
        raise Malformed("leading BOM", refusal="leading-bom")
    if re.search(r"\r(?!\n)", text):
        raise Malformed("lone CR: two rows would share one line", refusal="lone-cr")
    text = unicodedata.normalize("NFC", text)
    lines = split_lines(text)
    for n, line in enumerate(lines, 1):
        if line.startswith(CONFLICT):
            raise Malformed(f"line {n}: unresolved conflict marker", refusal="conflict-marker")
    tbl = []
    for line in lines:
        if line.strip(WSP).startswith("|"):
            if not line.strip(WSP).endswith("|"):
                raise Malformed(
                    f"table line lacks its closing pipe: {line.strip(WSP)!r}. §4.1.3 "
                    f"requires both, because only the closing pipe reveals a row "
                    f"truncated inside its final cell",
                    refusal="malformed-table-line",
                )
            tbl.append(line)
        elif tbl:
            break  # the run ended; §4 makes the table contiguous
    if not tbl:
        raise Malformed("no table found", refusal="no-table")
    # Membership only. `tbl` stays a list because §4's contiguous run is
    # ordered -- tbl[0] is the header and tbl[1] the alignment row -- but the
    # scan below asked `line not in tbl` once per line, which is a linear
    # search per line and quadratic over the file. Measured before this: 5k
    # rows 0.13s, 40k rows 6.58s -- 8x the rows for 50x the time.
    tbl_set = set(tbl)
    decls, order, key = {}, None, None
    order_seen = False
    for n, line in enumerate(lines, 1):
        if line.lstrip(WSP).startswith("#"):
            continue  # SPEC §9: the ignorable channel, inert whatever it contains
        stripped = _strip_annotation(line)
        if ":=" not in stripped:
            if stripped.strip(WSP) and line not in tbl_set:
                if stripped.strip(WSP).startswith("|"):
                    raise Malformed(
                        f"line {n}: this is a valid table line, but the table already "
                        f"ended above it. A table is a CONTIGUOUS run of lines beginning "
                        f"with '|' (§4.1.2), and an annotation or blank line between two "
                        f"rows ends it. Move the annotation above the table or below the "
                        f"declarations.",
                        refusal="unclassified-line",
                    )
                raise Malformed(
                    f"line {n}: not a table line, an annotation, or a declaration: "
                    f"{stripped.strip(WSP)!r}",
                    refusal="unclassified-line",
                )
            continue
        line = stripped
        if re.match(r"[ \t]*key[ \t]*:=[ \t]*\w+[ \t]*\(", line):
            # §4.1.11: `key := col` is key's only form. Read as `key := col`,
            # `key := sum(id)` would key the table on `id`.
            raise Malformed(
                f"line {n}: key takes a bare column name, not a function: {line.strip(WSP)!r}",
                refusal="malformed-declaration",
            )
        mw = re.match(r"[ \t]*([^\s:=]+)[ \t]*:=[ \t]*(\w+)\((.+)\)[ \t]*$", line)
        # §4.2: `arg = ident 1*WSP "where" 1*WSP pred`, so any run of space
        # and tab separates `where`, never only a single space.
        ww = re.search(r"[ \t]+where[ \t]+", mw.group(3)) if mw else None
        if ww:
            nm_, fn_, inner = mw.groups()
            col_, ptext = inner[: ww.start()], inner[ww.end() :]
            if not _is_ident(col_.lstrip(WSP)):
                # §4.1: only WSP may pad the aggregated column, never U+00A0,
                # and the column is an `ident`: a control or Cf character in
                # it is a malformed declaration, not a name that resolves to
                # no column.
                raise Malformed(
                    f"line {n}: malformed declaration: {line.strip(WSP)!r}",
                    refusal="malformed-declaration",
                )
            if "@" in ptext:
                raise Malformed(
                    f"line {n}: `@` names THIS ROW's value, and a declaration has no "
                    f"current row (SPEC §4.2 rule 5); {ptext.strip(WSP)!r} is malformed",
                    refusal="malformed-declaration",
                )
            _check_ident(nm_, "aggregate name")
            if nm_ in decls:
                raise Malformed(
                    f"line {n}: duplicate aggregate name {nm_!r}", refusal="duplicate-aggregate"
                )
            decls[nm_] = (fn_, col_.strip(WSP), ptext.strip(WSP))
            continue
        m = re.match(r"[ \t]*([^\s:=]+)[ \t]*:=[ \t]*(\w+)\([ \t]*([^\s()]*)[ \t]*\)[ \t]*$", line)
        if m:
            name, fn, arg = m.groups()
            if not _is_ident(arg):
                # §4.1: `arg = ident`, for `order := by(c)` as for an
                # aggregate. The pattern above admits any character but
                # whitespace and parentheses, and none at all, so a control or
                # Cf character, or nothing, would otherwise become a name that
                # resolves to no column: an aggregate of #REF!, or an order
                # that is never checked.
                raise Malformed(
                    f"line {n}: malformed declaration: {line.strip(WSP)!r}",
                    refusal="malformed-declaration",
                )
        else:
            m2 = re.match(r"[ \t]*([^\s:=]+)[ \t]*:=[ \t]*([\w.-]+)[ \t]*$", line)
            if not m2:
                raise Malformed(
                    f"line {n}: malformed declaration: {line.strip(WSP)!r}",
                    refusal="malformed-declaration",
                )
            name, fn, arg = m2.group(1), None, m2.group(2)
            if name not in ("key",):
                raise Malformed(
                    f"line {n}: {name!r} needs a function, e.g. {name} := sum(col)",
                    refusal="malformed-declaration",
                )
        if name == "order":
            # `order := none()` sets order to None, so a `None` test cannot see
            # a second declaration. Track that one was SEEN, not its value.
            if order_seen:
                raise Malformed(
                    f"line {n}: duplicate order declaration", refusal="duplicate-declaration"
                )
            order_seen = True
            if fn != "by":
                raise Malformed(
                    f"line {n}: order must be by(<column>); omit the line entirely "
                    f"for an unordered table",
                    refusal="malformed-declaration",
                )
            order = arg
        elif name == "key":
            if key is not None:
                raise Malformed(
                    f"line {n}: duplicate key declaration", refusal="duplicate-declaration"
                )
            key = arg
        else:
            _check_ident(name, "aggregate name")
            if name in decls:
                raise Malformed(
                    f"line {n}: duplicate aggregate name {name!r}", refusal="duplicate-aggregate"
                )
            decls[name] = (fn, arg, None)
    header = split_row(tbl[0])
    cols, formulas, seen = [], {}, set()
    for h in header:
        if "=" in h:
            nm, expr = h.split("=", 1)
            nm = nm.strip(WSP)
            cols.append(nm)
            formulas[nm] = expr.strip(WSP)
        else:
            cols.append(h)
    for c in cols:
        _check_ident(c, "column name")
        if c in seen:
            raise Malformed(f"duplicate column name {c!r}", refusal="duplicate-column")
        seen.add(c)
    # §9.12: a key names a stored column, or the declaration is malformed.
    if key is not None:
        if key not in cols:
            raise Malformed(f"key := {key} names no column", refusal="malformed-declaration")
        if key in formulas:
            raise Malformed(f"key := {key} is a computed column", refusal="malformed-declaration")
    # I7: row-relative operators are illegal unless order is declared
    for nm, expr in formulas.items():
        for fn in ROWREL:
            # §4.2 rule 4: a function name touches its `(`. `prior (n)` is
            # not a row-relative call, and is refused as a formula below.
            if re.search(rf"\b{fn}\(", expr):
                if order is None:
                    raise Malformed(
                        f"column {nm!r} uses row-relative {fn}() but the table "
                        f"declares no row order. Add `order := by(<column>)`.",
                        refusal="rowrel-without-order",
                    )
                if order not in cols:
                    raise Malformed(
                        f"order := by({order}) but there is no column {order!r}",
                        refusal="bad-order-column",
                    )
    if len(tbl) < 2:
        raise Malformed("table has no alignment row", refusal="bad-alignment-row")
    if not is_align(tbl[1]):
        raise Malformed(
            f"the second table line is not a valid alignment row: {tbl[1].strip(WSP)!r}. "
            f"Cells must be one of ---, :--, --:, :-:",
            refusal="bad-alignment-row",
        )
    if len(split_row(tbl[1])) != len(cols):
        raise Malformed(
            f"alignment row has {len(split_row(tbl[1]))} fields, header has {len(cols)}",
            refusal="alignment-field-count",
        )
    rows = []
    for line in tbl[2:]:
        if is_align(line):
            raise Malformed(
                f"alignment-style row among the data rows "
                f"(wrong number of value fields): {line.strip(WSP)!r}",
                refusal="alignment-row-in-data",
            )
        v = split_row(line)
        if len(v) != len(cols):
            raise Malformed(
                f"row has {len(v)} fields, header has {len(cols)}: {line.strip(WSP)!r}",
                refusal="row-field-count",
            )
        row = dict(zip(cols, v, strict=False))
        for c, cell in row.items():
            if cell.startswith("#REF!"):
                row[c] = _Text(cell)
        for c in formulas:
            # `split_row` has trimmed the cell of ASCII space and tab, which
            # is all §4.1.4 trims. A second `.strip()` here also removed
            # U+00A0 and the other Unicode spaces, so a computed cell holding
            # only one was read as empty instead of as a value (§9.17).
            if row.get(c, "") != "":
                raise Malformed(
                    f"computed column {c!r} has a value {row[c]!r} in a data row; "
                    f"computed cells must be empty",
                    refusal="value-in-computed-cell",
                )
        rows.append(row)
    if key:
        for r in rows:
            if str(r.get(key, "")) == "":
                # §4.1.9: an ident is one or more characters, so a blank key
                # is not one -- and it must not fall through to §9.5, where
                # two blanks would be called duplicates of each other.
                raise Malformed(
                    f"row key {key}= is blank; a row id is an ident of one or "
                    f"more letters, marks, digits or underscores (§4.1.9)",
                    refusal="bad-identifier",
                )
            _check_ident(str(r.get(key, "")), f"row key {key}=")
        ids = [r.get(key) for r in rows]
        if len(set(ids)) != len(ids):
            dup = [i for i in ids if ids.count(i) > 1][0]
            raise Malformed(f"duplicate key {key}={dup!r}", refusal="duplicate-row-id")
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
    vals = [str(r.get(col, "")) for r in rows]
    if any(v == "" for v in vals):
        # §6: blank is none of number/date/text, so a column mixing it with any
        # of them mixes types. Previously blanks were filtered out here and the
        # sort then called `num("")` on them, raising an uncaught ValueError --
        # neither a value nor a refusal, which §8's totality forbids.
        raise Malformed(
            f"order column {col!r} has a blank cell; an ordering column must "
            f"have a single type across every row (§9.10), and blank is none "
            f"of number, date or text",
            refusal="bad-order-column",
        )
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
            f"an ordering column must have a single type",
            refusal="bad-order-column",
        )
    return kinds.pop()


_GROUP = re.compile(r"(\w+)\([ \t]*(\w+)[ \t]+where[ \t]+(.+?)[ \t]*\)[ \t]*$")
_PRED = re.compile(r'(\w+)[ \t]*=[ \t]*(?:@(\w+)|"([^"]*)")')


def _predicate(text, cols, computed, refusal):
    """A conjunction of equality predicates. `@c` is THIS ROW's value of c.

    `refusal` is the §9 identifier for a predicate the grammar does not
    generate, which depends on where it is written: a header cell or a
    declaration line."""
    preds, unknown = [], None
    for part in [x.strip(WSP) for x in re.split(r"[ \t]+and[ \t]+", text)]:
        m = _PRED.fullmatch(part)
        if not m:
            raise Malformed(f"unsupported predicate {part!r}", refusal=refusal)
        col, at, lit = m.groups()
        for c in (col, at):
            if c and c not in cols:
                # §8: a name that does not resolve is #REF!(name), here as
                # anywhere. Refusing would make the file's ACCEPTANCE depend on
                # the header rather than on its own bytes -- §4.2 rule 7's
                # argument, which it made for the aggregated column and which
                # applies unchanged to the predicate's. Raised only after
                # every part is checked: a refusal anywhere in the predicate
                # outranks a #REF!, which is a value.
                unknown = unknown or c
            elif c and c in computed:
                raise Malformed(
                    f"predicate names computed column {c!r} (§9.22): comparison is on "
                    f"cell text and a computed column has none, so the predicate would "
                    f"match nothing and `sum` would report a plausible 0",
                    refusal="computed-column-compared",
                )
        preds.append((col, at, lit))
    if unknown:
        raise KeyError(unknown)  # the leftmost, per §8
    return preds


def _exact(nums, divisor):
    """§7: the correctly-rounded binary64 value of the EXACT sum, over `divisor`.

    Defined on the multiset, so it cannot depend on the order rows sit in --
    §6 promises shuffling every line changes nothing, and a left-to-right
    accumulation of the same four cells gives 0 in one order and an overflow in
    another. `avg` divides the EXACT sum, not the rounded one, so a mean that is
    finite stays finite even where the sum is not: four cells of 1e308 average
    to 1e308.

    `math.fsum` is exact and order-independent for a finite result, so it is the
    fast path. It refuses when a PARTIAL sum leaves range even if later terms
    bring it back, which is the one case it cannot answer -- and where the exact
    sum is what the rule asks for anyway.
    """
    if divisor == 1:
        try:
            return math.fsum(nums)
        except OverflowError:
            pass
    # Exact, and O(n). Every finite binary64 is an integer times a power of two,
    # so putting them over a common power-of-two denominator makes the sum one
    # big-integer addition per value, with no rounding anywhere. Summing
    # `Fraction`s instead is O(n^2) -- it renormalises by gcd on every addition,
    # and measured 45s on 100k rows against 0.5s on 10k.
    parts = [float(x).as_integer_ratio() for x in nums]
    den = max(d for _, d in parts)
    num = sum(n * (den // d) for n, d in parts)
    try:
        # int/int true division is correctly rounded in CPython, so this is the
        # single rounding the rule asks for: of the exact sum, or of the exact
        # MEAN when a divisor is given -- which is why `avg` stays finite where
        # `sum` overflows.
        return num / (den * divisor)
    except OverflowError:
        return float("inf")  # the caller maps a non-finite result to #REF!(overflow)


# §8: of several #REF! among one aggregate's operands, the first by shape in
# this order, then the name that sorts first. Never the first row's.
_REF_RANK = {"cycle": 0, "/0": 2, "empty": 3, "overflow": 4}


def _first_ref(errs):
    return min(errs, key=lambda e: (_REF_RANK.get(e[6:-1], 1), e[6:-1]))


def _agg(fn, vals, what):
    bad = [v for v in vals if _is_ref(v)]
    # `count` counts rows and never coerces: it is poisoned by a #REF! already
    # present but not by a value that merely is not a number, because it never
    # uses one as an operand.
    if fn != "count":
        for v in vals:
            if v in ("", None) or _is_ref(v):
                continue
            try:
                x = num(v)
            except (ValueError, TypeError):
                bad.append(f"#REF!({what})")
                continue
            if not math.isfinite(x):
                # §8: a stored cell whose binary64 value is infinite is
                # #REF!(overflow) wherever it is an operand. `fsum` raises on
                # inf + -inf, and `_exact` cannot take an infinity's integer
                # ratio, so it must not reach them.
                bad.append("#REF!(overflow)")
    if bad:
        return _first_ref(bad)
    if fn == "count":
        return len(vals)
    nums = [num(v) for v in vals if v not in ("", None)]
    if fn == "sum":
        got = _exact(nums, 1)
    elif fn == "avg":
        if not nums:
            return "#REF!(empty)"
        got = _exact(nums, len(nums))
    elif not nums:
        return "#REF!(empty)"
    else:
        got = min(nums) if fn == "min" else max(nums)
    if got in (float("inf"), float("-inf")):
        # §8. Stated separately from §4.2 rule 2 because an aggregate is not an
        # `expr` operation: a sum of a million large-but-finite cells overflows
        # without any single operation doing so. Returning `inf` would write a
        # value §4.1.6 cannot spell, so `canon` could not round-trip its own
        # output.
        return "#REF!(overflow)"
    return got


def _ast(expr, where):
    # §4.2 rule 8 refuses a `#` outside the grammar. Inside a `string` it is a
    # character like any other (rule 6), so `if(a = "#4", 1, 2)` is a formula.
    if "#" in re.sub(r'"[^"]*"', "", expr):
        raise Malformed(
            f"column {where!r}: '#' is not a comment inside a formula (§4.1.10); "
            f"a whole-line annotation goes outside the table",
            refusal="malformed-formula",
        )
    return _parse_expr(expr, where)


_TOK = re.compile(
    r"[ \t]*(?:(?P<str>\"[^\"]*\")"
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
                    f"total two ways",
                    refusal="malformed-formula",
                )
            raise Malformed(
                f"column {where!r}: {ch!r} is not part of an expression; §4.2 admits "
                f"column names, unsigned decimal literals, + - * / and parentheses",
                refusal="malformed-formula",
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
                    f"column {where!r}: parentheses nested deeper than {MAX_NESTING} (§9.23)",
                    refusal="nesting-too-deep",
                )
            eat(v)
            e = sum_()
            depth -= 1
            if peek() != ("op", ")"):
                raise Malformed(
                    f"column {where!r}: unclosed parenthesis", refusal="malformed-formula"
                )
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
                f"§4.2 admits + - * / and unary minus",
                refusal="malformed-formula",
            )
        raise Malformed(
            f"column {where!r}: expected a value in {expr!r}", refusal="malformed-formula"
        )

    def want(tok, what):
        if peek() != tok:
            raise Malformed(
                f"column {where!r}: expected {what} in {expr!r}", refusal="malformed-formula"
            )
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
                f"column name (§4.2 rule 10)",
                refusal="malformed-formula",
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
                    f"refused for §4.1.6's reason",
                    refusal="malformed-formula",
                )
            raise Malformed(
                f"column {where!r}: if() takes a comparison first (§4.2 rule 10); "
                f"admitted operators are < <= > >= = <>",
                refusal="malformed-formula",
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
                f"right of {op!r} (§4.2 rule 10)",
                refusal="malformed-formula",
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
                    f"locale-dependent, so two conforming readers would disagree",
                    refusal="malformed-formula",
                )
            else:
                raise Malformed(
                    f"column {where!r}: expected a value after {op!r}", refusal="malformed-formula"
                )
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
                    f"unequal as text",
                    refusal="ident-compared-in-if",
                )
            else:
                raise Malformed(
                    f"column {where!r}: expected a value after {op!r}", refusal="malformed-formula"
                )
        eat(v3)
        return Cmp(op, lhs, kind, rhs)

    def cond():
        nonlocal pos, depth
        k, name = peek()
        if name != "if":
            raise Malformed(
                f"column {where!r}: unknown function {name!r}; §4.2 admits if() in an "
                f"expression, and cumulative/prior/delta/sum/count/min/max/avg as the "
                f"whole formula",
                refusal="malformed-formula",
            )
        eat(name)
        depth += 1
        if depth > MAX_NESTING:
            raise Malformed(
                f"column {where!r}: nested deeper than {MAX_NESTING} (§9.23)",
                refusal="nesting-too-deep",
            )
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
            raise Malformed(
                f"column {where!r}: unary + is not in §4.2; write the value without it",
                refusal="malformed-formula",
            )
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
                f"format has numbers and errors and no boolean for {expr!r} to have",
                refusal="malformed-formula",
            )
        raise Malformed(
            f"column {where!r}: trailing input in {expr!r}", refusal="malformed-formula"
        )
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
    if _is_ref(v) and v.startswith("#REF!(") and v.endswith(")"):
        raise KeyError(v[6:-1])
    return v


def _number(name, env):
    v = _cell(name, env)
    if v == "":
        raise KeyError(name)
    try:
        got = num(v)
    except (ValueError, TypeError):
        raise KeyError(name) from None
    if got in (INF, -INF):
        # §8: a stored cell whose decimal spelling is finite but whose binary64
        # value is not is #REF!(overflow) wherever it is used as an operand.
        # Passed on, it reached the output as `inf`, or as `nan` once two met.
        raise KeyError("overflow")
    return got


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
        if c.rhs in (INF, -INF):
            # A `signed` bound too long for binary64 is #REF!(overflow) like any
            # other operand (§4.2 rule 2). The left-hand side goes first: its
            # error is the leftmost (§8).
            raise KeyError("overflow")
        return eq if c.op == "=" else not eq
    a = _number(c.lhs, env)
    b = c.rhs if c.kind == "num" else _number(c.rhs, env)
    if b in (INF, -INF):
        raise KeyError("overflow")
    if c.op == "<":
        return a < b
    if c.op == "<=":
        return a <= b
    if c.op == ">":
        return a > b
    return a >= b


def ev(node, env):
    if isinstance(node, Num):
        if node.v in (INF, -INF):
            # §4.2 rule 2 stores no infinity, and a `literal` of four hundred
            # digits is one: `999...9 * 0` was `nan`.
            raise KeyError("overflow")
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
    """Every column this formula MENTIONS, in TEXTUAL order, both branches of
    every `if`.

    Order is load-bearing: §8 decides which `#REF!` a formula carries by
    position in the formula text, precisely so that the answer cannot depend on
    an evaluation strategy that §4.2 rule 9 makes a free choice. Callers that
    want a set build one from this list; there is deliberately no second walker.

    §4.2 rule 10: evaluation is lazy but dependency and cycle analysis is
    static. If the untaken branch were excluded, whether a table has a cycle
    would depend on its data, so one inserted row could turn a working table
    cyclic -- and two branches inserting different rows could disagree about
    it, which is the silent-wrong merge the format exists to remove.
    """
    if out is None:
        out = []

    def add(n):
        if n not in out:
            out.append(n)

    if isinstance(node, Name):
        add(node.id)
    elif isinstance(node, Neg):
        names_of(node.x, out)
    elif isinstance(node, Bin):
        names_of(node.l, out)
        names_of(node.r, out)
    elif isinstance(node, If):
        add(node.c.lhs)
        if node.c.kind == "name":
            add(node.c.rhs)
        names_of(node.a, out)
        names_of(node.b, out)
    return out


OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
}


def _header_error(node, known):
    """The leftmost error a formula has whatever the data: a name that does not
    resolve, or a literal whose binary64 value is infinite (§4.2 rule 10, §8).
    Both branches of every `if`, in textual order."""
    if isinstance(node, Name):
        return None if node.id in known else f"#REF!({node.id})"
    if isinstance(node, Num):
        return "#REF!(overflow)" if node.v in (INF, -INF) else None
    if isinstance(node, Neg):
        return _header_error(node.x, known)
    if isinstance(node, Bin):
        return _header_error(node.l, known) or _header_error(node.r, known)
    if isinstance(node, If):
        c = node.c
        err = None if c.lhs in known else f"#REF!({c.lhs})"
        if err is None and c.kind == "name" and c.rhs not in known:
            err = f"#REF!({c.rhs})"
        if err is None and c.kind == "num" and c.rhs in (INF, -INF):
            err = "#REF!(overflow)"
        return err or _header_error(node.a, known) or _header_error(node.b, known)
    return None


def _plain_column(nm, tree, err, seq):
    """An ordinary formula, row by row. Every column it names already holds its
    values: `_evaluate_columns` reaches it only after them."""
    for r in seq:
        if err:
            # §4.2 rule 10: a header error is the same answer in every row.
            r[nm] = err
            continue
        try:
            r[nm] = ev(tree, r)
        except KeyError as e:
            r[nm] = f"#REF!({e.args[0]})"


def _rowrel_column(nm, fn, src, seq, formulas, cols):
    """`prior`, `delta` or `cumulative` over the DERIVED order (§6, §7).

    `src` already holds its values, as the types they were computed as: a
    computed number is a float and is never re-read through its printed form,
    which §4.1.6's cell grammar would refuse (`1e-05`), and a computed error
    carries the name it originated with (§8).
    """
    if src not in cols:
        # §4.2 rule 10: whether `src` resolves is a property of the header,
        # so it is #REF!(src) in every row, the first included.
        for r in seq:
            r[nm] = f"#REF!({src})"
        return
    # Each operator depends on a DIFFERENT thing, and collapsing them into
    # one "is this row's cell a number?" guard got two of the three wrong:
    #   prior       needs only the PRECEDING row's value -- not this one
    #   delta       needs both, as numbers
    #   cumulative  needs every value so far, so one bad cell poisons the
    #               rest of the column rather than being stepped over
    # §8 forbids a stale value, and skipping a blank row produced exactly
    # one: `prior` reported a number true two rows ago, and `cumulative`
    # resumed as though the blank had not happened.
    acc, prev, poisoned = 0.0, None, None
    prev_ovf = False
    prev_err = None
    for r in seq:
        raw = r.get(src, "")
        try:
            v = num(raw)
        except (ValueError, TypeError):
            v = None
        # §8: a stored cell whose binary64 value is infinite is
        # #REF!(overflow) as an operand. Passed on, `delta` subtracted two
        # infinities into `nan` and `prior` stored `inf`.
        ovf = v in (INF, -INF)
        # This row's value as an operand: its own error, or None. A
        # computed source carries the error it originated, not #REF!(src).
        if _is_ref(raw):
            err = raw
        elif ovf:
            err = "#REF!(overflow)"
        elif v is None:
            err = f"#REF!({src})"
        else:
            err = None
        if fn == "prior":
            # `prev` is None only before the first row; after that it is the
            # preceding row's value, blank included.
            if prev is None:
                r[nm] = ""
            else:
                r[nm] = "#REF!(overflow)" if prev_ovf else prev
        elif fn == "delta":
            # §7: `delta(c)` is `c - prior(c)`, so by §8's leftmost rule
            # this row's error wins over the preceding row's -- in the first
            # row too, where it is blank only when `c` is a number.
            if prev is None:
                r[nm] = err or ""
            elif err or prev_err:
                r[nm] = err or prev_err
            else:
                d = v - prev
                r[nm] = "#REF!(overflow)" if d in (INF, -INF) else d
        elif fn == "cumulative":
            # The first bad CELL sets the error for the rest of the column,
            # and it is that cell's own error (§8). An overflow of the
            # running total itself is not a bad cell: it is `acc` below,
            # and a later blank still makes it #REF!(c), as in `rowspec_alt`.
            # SPEC.md does not order the two.
            if poisoned is None and (v is None or ovf):
                poisoned = err
            if poisoned:
                r[nm] = poisoned
            else:
                acc += v
                # §8: `inf` is not a `number` under §4.1.6, so storing one
                # writes a file this implementation could not read back and
                # `canon` would not round-trip its own output.
                r[nm] = "#REF!(overflow)" if acc in (INF, -INF) else acc
        prev = raw if v is None else v
        if v is None and raw != "" and src not in formulas:
            # §4.2 rule 10: a computed value is a number or an error, so
            # stored text that will not coerce is #REF!(src) (§8), never
            # the text itself -- which `count` would then count as a value.
            prev = f"#REF!({src})"
        prev_ovf = ovf
        prev_err = err


def _group_column(nm, fn, col, ptext, seq, formulas, cols):
    """A per-row group aggregate (§7). `col` already holds its values: a
    computed one is aggregated by what it evaluated to, never by its (always
    empty) stored cells (§4.2 rule 5)."""
    try:
        preds, missing = _predicate(ptext, cols, formulas, "malformed-formula"), None
    except KeyError as e:
        preds, missing = None, e.args[0]
    if col not in cols:
        # §8: a name that does not resolve is #REF!(name), not a
        # refusal -- §4.2 rule 7's argument -- and the aggregated
        # column is leftmost, ahead of any name in the predicate.
        missing = col
    if missing:
        for r in seq:
            r[nm] = f"#REF!({missing})"
        return
    for r in seq:

        def hit(o, r=r, preds=preds):
            return all(
                str(o.get(pc, "")) == (str(r.get(at, "")) if at else lit) for pc, at, lit in preds
            )

        r[nm] = _agg(fn, [o.get(col) for o in seq if hit(o)], col)


def _evaluate_columns(seq, cols, formulas):
    """Every computed column, by DEPENDENCY over one graph (§4.2 rule 9).

    Ordinary formulas, row-relative columns and group aggregates are nodes of
    the same graph, and a column is evaluated, for every row at once, only
    when every computed column it names already holds its values. So header
    order is never an input to a value, and what is left once nothing more is
    ready is on a cycle or depends on one -- through a `prior` or a group
    aggregate as much as through arithmetic. Evaluated in passes by kind
    instead, a row-relative column read a later one, or a group aggregate,
    before it had a value.

    Readiness is decided from the STATIC name set, not from whether an
    evaluation happens to raise. With `if` that distinction is load-bearing:
    a lazy branch can compute a value without ever touching a column the
    formula still depends on, and a trial-and-error fixpoint would then commit
    that value before finding out the column was on a cycle. And a blank is
    never read as "not computed yet": `prior`'s first row is blank by
    definition.
    """
    computed = frozenset(formulas)
    rowrel, groups, plain = {}, {}, {}
    for nm, expr in formulas.items():
        # §4.2: `rowrel-call = rowrel-fn "(" ...`, with no WSP before `(`
        # (rule 4). Admitting it here read `prior (n)` as `prior(n)`.
        m = re.fullmatch(r"[ \t]*(\w+)\([ \t]*(\w+)[ \t]*\)[ \t]*", expr)
        g = _GROUP.fullmatch(expr.strip(WSP))
        if m and m.group(1) in ROWREL:
            rowrel[nm] = m.groups()
        elif g:
            groups[nm] = g.groups()
        else:
            plain[nm] = expr
    # Refusals first, all of them static. Parsed once per table rather than
    # once per cell per row: the trees are pure, and re-parsing was the
    # evaluator's dominant cost. It also means a malformed formula is refused
    # on a table with no rows, which it must be -- §9.20 is about the bytes,
    # and acceptance may not depend on the data.
    trees = {nm: _ast(expr, nm) for nm, expr in plain.items()}
    for nm, t in trees.items():
        for c in sorted(str_cmp_lhs(t) & computed):
            raise Malformed(
                f"column {nm!r}: if() compares computed column {c!r} against a "
                f"string (§9.22). A computed column has no cell text, so the only "
                f"reading left compares against a rendered number and §2 leaves "
                f"rendering to the implementation -- one reader matches {c!r} and "
                f"another does not, and both report a number. Compare it against a "
                f"numeric literal instead",
                refusal="computed-column-compared",
            )
    for nm, (fn, _col, ptext) in groups.items():
        if fn not in ("sum", "count", "min", "max", "avg"):
            raise Malformed(
                f"unknown aggregate {fn!r} in column {nm!r}", refusal="unknown-aggregate"
            )
        # The predicate here, ahead of any value: it depends only on the
        # header, and a refusal in it must fire whether or not the aggregate
        # ever gets a value -- a source on a cycle included.
        try:
            _predicate(ptext, cols, computed, "malformed-formula")
        except KeyError:
            pass  # a name that does not resolve is a value, given below
    # §4.2 rule 10: whether a name RESOLVES is a property of the header, so it
    # is the same answer in every row -- including a row whose `if` selects the
    # other branch. Otherwise a merge that adds the first row taking that branch
    # poisons the column, and every aggregate over it, without touching a
    # formula or a header.
    # A literal too long for binary64 is the same kind of error (§8): its cause
    # is in the header, so it is #REF!(overflow) in every row too.
    known = set(cols)
    # §8: the LEFTMOST such error in the formula text, not the alphabetically
    # first and not whichever one evaluation reached first -- rule 9 makes
    # evaluation strategy a free choice, so the error must not be a function
    # of it.
    unresolved = {nm: _header_error(t, known) for nm, t in trees.items()}
    # One graph. Dependency and cycle analysis is over the whole formula, both
    # branches of every `if` included (§4.2 rule 10), and a row-relative or
    # group column depends on the column it reads. A group predicate names
    # stored columns only (§9.22), so it adds no edge.
    deps = {nm: names_of(t) for nm, t in trees.items()}
    for nm, (_fn, src) in rowrel.items():
        deps[nm] = [src]
    for nm, (_fn, col, _ptext) in groups.items():
        deps[nm] = [col]
    deps = {nm: set(d) & computed for nm, d in deps.items()}
    pending = set(formulas)
    while pending:
        progressed = False
        for nm in sorted(pending):
            if deps[nm] & pending:
                continue  # waits on a pending column, itself included
            if nm in trees:
                _plain_column(nm, trees[nm], unresolved[nm], seq)
            elif nm in rowrel:
                _rowrel_column(nm, *rowrel[nm], seq, formulas, cols)
            else:
                _group_column(nm, *groups[nm], seq, formulas, cols)
            pending.discard(nm)
            progressed = True
        if not progressed:
            break
    # §4.2 rule 9: what never became ready is on a cycle or depends on one.
    for nm in pending:
        for r in seq:
            r[nm] = "#REF!(cycle)"


def evaluate(text):
    cols, formulas, rows, decls, order, key = parse(text)
    # THE ORDERING: derived from data, then row id as a stable tiebreak.
    if order:
        if key is None:
            raise Malformed(
                "`order := by(...)` requires a `key :=` declaration: "
                "without one, tied order values fall back to physical "
                "file position, which is a coordinate",
                refusal="order-without-key",
            )
        if order in formulas:
            raise Malformed(
                f"`order := by({order})` names a COMPUTED column; "
                f"ordering must be derived from stored data",
                refusal="bad-order-column",
            )
        kind = column_type(order, rows)

        def typed(r):
            v = str(r[order])
            if kind == "number":
                f = num(v)
                if f != f or f in (float("inf"), float("-inf")):
                    raise Malformed(
                        f"order column {order!r} contains {v!r}", refusal="bad-order-column"
                    )
                return f
            if kind == "date":
                y, m, d = (int(x) for x in re.split(r"[-/]", v))
                return (y, m, d)
            return v

        # a real TUPLE, never a concatenation: the key breaks ties and nothing else
        seq = sorted(rows, key=lambda r: (typed(r), str(r.get(key, ""))))
    else:
        seq = rows
    _evaluate_columns(seq, cols, formulas)
    # table-level aggregates, once every column holds its values
    out = {}
    for nm, (fn, col, pred) in decls.items():
        # Refusals first: a missing column is a #REF!, which is a value, and
        # must not hide an unknown function or a predicate §9 refuses.
        if fn not in ("sum", "count", "min", "max", "avg"):
            raise Malformed(
                f"unknown aggregate function {fn!r} in {nm!r}", refusal="unknown-aggregate"
            )
        try:
            preds_ = _predicate(pred, cols, formulas, "malformed-declaration") if pred else None
        except KeyError as e:
            preds_ = e
        # The leftmost name: the aggregated column precedes the predicate.
        if col not in cols:
            out[nm] = f"#REF!({col})"
            continue
        if isinstance(preds_, KeyError):
            out[nm] = f"#REF!({preds_.args[0]})"
            continue
        rows_ = seq
        if pred:
            rows_ = [
                o
                for o in seq
                if all(
                    str(o.get(pc, "")) == (str(o.get(at, "")) if at else lit)
                    for pc, at, lit in preds_
                )
            ]
        vals = [r.get(col) for r in rows_]
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
    lines = split_lines(text, keepends=True)
    cols, formulas, rows, decls, order, key = parse(text)
    tbl_idx = [i for i, ln in enumerate(lines) if ln.strip(WSP).startswith("|")]
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
        aligns = [a.strip(WSP) for a in split_row(st["align_raw"])]
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
    # §4.1.1: canon normalises EVERY terminator to LF. `prefix` and `tail` carry
    # annotations and declarations through byte-verbatim, which on a CRLF file
    # left them CRLF while the table lines emitted above are LF -- a canonical
    # form with mixed terminators, which §3 says is not canonical at all, and
    # which made canon's own output something a second reader would canonicalise
    # differently. "Byte-verbatim" is about what a line says, not how it ends.
    return "".join(out).replace("\r\n", "\n").replace("\r", "\n")


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
        raise Malformed(f"{col!r} is a computed column", refusal="value-in-computed-cell")
    idx = st["cols"].index(col)
    for i, r in enumerate(st["rows"]):
        if str(r.get(key)) == str(row_key):
            r[col] = str(value)
            cells = split_row(st["row_raws"][i])
            cells[idx] = str(value)
            st["row_raws"][i] = "| " + " | ".join(escape_cell(c) for c in cells) + " |\n"
            return st
    raise Malformed(f"no row with {key}={row_key!r}")
