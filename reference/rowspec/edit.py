# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Edit a `.mdtbl` file with the smallest text diff the format allows.

Git merges by line, and two changes merge cleanly only when an unchanged line
separates them. Every function here therefore changes only the lines its
operation is about, and inside those lines only the cells or spans concerned:
nothing is re-rendered, re-aligned or canonicalised. docs/editing-api.md has the
rules and the shape of each operation's diff.

Every function is text in, text out, and refuses before returning anything:
the input must be a file SPEC.md accepts, and so must the output.
"""

import re
import secrets
import unicodedata

from .table import (
    _GROUP,
    _LITERAL,
    _PRED,
    _TOK,
    _UNESCAPED_PIPE,
    ROWREL,
    WSP,
    Malformed,
    _check_ident,
    _strip_annotation,
    escape_cell,
    evaluate,
    parse,
    split_lines,
    split_row,
)


class EditRefused(Malformed):
    """An edit the API will not make for a reason of its own, not one of SPEC.md
    §9's refusals. `reason` names it; `refusal` stays None."""

    def __init__(self, reason, message):
        super().__init__(message)
        self.reason = reason


def _nfc(s):
    return unicodedata.normalize("NFC", s)


def _eol(line):
    if line.endswith("\r\n"):
        return "\r\n"
    return "\n" if line.endswith("\n") else ""


def _body(line):
    return line[: len(line) - len(_eol(line))]


def _text_value(v, what):
    if not isinstance(v, str):
        raise TypeError(f"{what} must be a str, not {type(v).__name__}")
    if "\r" in v or "\n" in v:
        raise EditRefused("line-break", f"{what} {v!r} contains a line break (§4.1)")
    return _nfc(v)


def _cell_value(v, what):
    v = _text_value(v, what)
    if v != v.strip(WSP):
        raise EditRefused(
            "not-representable",
            f"{what} {v!r} has leading or trailing space or tab, which a cell trims (§4.1.4)",
        )
    return v


def _spans(body):
    """The (start, end) of each cell's raw text in a table line's body, exactly
    where `split_row` splits it."""
    stripped = body.strip(WSP)
    start = len(body) - len(body.lstrip(WSP))
    end = start + len(stripped)
    if stripped.startswith("|"):
        start += 1
    if stripped.endswith("|") and not stripped.endswith("\\|"):
        end -= 1
    cuts = [start] + [m.start() for m in _UNESCAPED_PIPE.finditer(body, start, end)] + [end]
    return [(cuts[0] if i == 0 else cuts[i] + 1, cuts[i + 1]) for i in range(len(cuts) - 1)]


def _padded(inner):
    return len(inner) > len(inner.strip(WSP)) + 2


def _pad(text, width, align):
    """`text` padded to `width` characters, as a column aligned `align` is."""
    room = width - len(text) - 2
    if room <= 0:
        out = f" {text} "
    elif align == "right":
        out = " " * (room + 1) + text + " "
    elif align == "center":
        out = " " * (room // 2 + 1) + text + " " * (room - room // 2 + 1)
    else:
        out = " " + text + " " * (room + 1)
    return out


def _refill(old, text):
    """`text` in place of a cell whose raw text was `old`: the same padding, and
    the same width when `text` fits."""
    if not _padded(old):
        if not old.strip(WSP):
            out = f" {text} "
        else:
            lead = len(old) - len(old.lstrip(WSP))
            trail = len(old) - len(old.rstrip(WSP))
            out = old[:lead] + text + old[len(old) - trail :]
    else:
        lead = len(old) - len(old.lstrip(WSP))
        trail = len(old) - len(old.rstrip(WSP))
        if old.strip(WSP) and lead > 1 and trail > 1:
            align = "center"
        elif old.strip(WSP) and lead > 1:
            align = "right"
        else:
            align = "left"
        out = _pad(text, len(old), align)
    # A backslash right before a pipe would escape it (§4.1.3).
    return out + " " if out.endswith("\\") else out


def _replace(body, edits):
    """Apply (start, end, text) edits to `body`, which must not overlap."""
    for a, b, t in sorted(edits, reverse=True):
        body = body[:a] + t + body[b:]
    return body


def _align_kind(cell):
    c = cell.strip(WSP)
    if c.startswith(":") and c.endswith(":") and len(c) > 1:
        return "center"
    return "right" if c.endswith(":") else "left"


_ROWREL_CALL = re.compile(r"[ \t]*(\w+)\([ \t]*(\w+)[ \t]*\)[ \t]*")


def _formula_refs(f):
    """Every column name a header formula mentions, as (start, end, name,
    operand): the span of the name in `f`, and whether it stands where a token
    spelled like a number would be read as one (§4.2 rule 7). Recognised as
    `_evaluate_columns` recognises it: row-relative call, group call, then
    expression."""
    m = _ROWREL_CALL.fullmatch(f)
    if m and m.group(1) in ROWREL:
        return [(m.start(2), m.end(2), m.group(2), False)]
    lead = len(f) - len(f.lstrip(WSP))
    g = _GROUP.fullmatch(f.strip(WSP))
    if g:
        out = [(lead + g.start(2), lead + g.end(2), g.group(2), False)]
        base = lead + g.start(3)
        for p in _PRED.finditer(g.group(3)):
            out.append((base + p.start(1), base + p.end(1), p.group(1), False))
            if p.group(2):
                out.append((base + p.start(2), base + p.end(2), p.group(2), False))
        return out
    toks, i = [], 0
    while i < len(f):
        m = _TOK.match(f, i)
        if not m or m.end() == i:
            break
        i = m.end()
        if m.group("word") is not None:
            kind = "call" if f[i : i + 1] == "(" else "word"
            toks.append((kind, m.group("word"), m.start("word"), m.end("word")))
        elif m.group("op") is not None:
            toks.append(("op", m.group("op"), m.start("op"), m.end("op")))
        else:
            toks.append(("other", m.group(), m.start(), m.end()))
    out = []
    for n, (kind, text, a, b) in enumerate(toks):
        if kind != "word":
            continue
        # `comparison = ident ...`: the left of an `if` comparison is a name
        # position, so a bare `3` there is the column named 3.
        if n >= 2 and toks[n - 2][:2] == ("call", "if") and toks[n - 1][:2] == ("op", "("):
            out.append((a, b, text, False))
        elif not _LITERAL.match(text):
            out.append((a, b, text, True))
    return out


_DECL_HEAD = re.compile(r"[ \t]*([^\s:=]+)[ \t]*:=[ \t]*")
_DECL_WHERE = re.compile(r"[ \t]*([^\s:=]+)[ \t]*:=[ \t]*(\w+)\((.+)\)[ \t]*$")
_DECL_CALL = re.compile(r"[ \t]*([^\s:=]+)[ \t]*:=[ \t]*(\w+)\([ \t]*([^\s()]*)[ \t]*\)[ \t]*$")
_DECL_BARE = re.compile(r"[ \t]*([^\s:=]+)[ \t]*:=[ \t]*([\w.-]+)[ \t]*$")


def _declaration(body):
    """(name, rhs start, rhs end, refs) for a declaration line, or None. Read
    with `parse`'s own patterns, so a span here is what `parse` reads."""
    if body.lstrip(WSP).startswith("#"):
        return None
    s = _strip_annotation(body)
    if ":=" not in s:
        return None
    h = _DECL_HEAD.match(s)
    rhs_end = len(s.rstrip(WSP))
    refs = []
    mw = _DECL_WHERE.match(s)
    ww = re.search(r"[ \t]+where[ \t]+", mw.group(3)) if mw else None
    if ww:
        col = mw.group(3)[: ww.start()]
        a = mw.start(3) + len(col) - len(col.lstrip(WSP))
        refs.append((a, a + len(col.strip(WSP)), col.strip(WSP), False))
        pred = mw.group(3)[ww.end() :]
        base = mw.start(3) + ww.end()
        for p in _PRED.finditer(pred):
            refs.append((base + p.start(1), base + p.end(1), p.group(1), False))
    elif m := _DECL_CALL.match(s):
        refs.append((m.start(3), m.end(3), m.group(3), False))
    elif m := _DECL_BARE.match(s):
        refs.append((m.start(2), m.end(2), m.group(2), False))
    return _nfc(h.group(1)), h.end(), rhs_end, refs


class _Doc:
    """A file SPEC.md accepts, as its lines with their terminators."""

    def __init__(self, text):
        evaluate(text)
        self.cols, self.formulas, _rows, _decls, self.order, self.key = parse(text)
        self.lines = split_lines(text, keepends=True)
        self.index()

    def index(self):
        """Find the table again. Called after every insertion, so no index goes
        stale when a line is added above the table. A removal is always the
        edit's last step, so nothing reads an index after one."""
        tbl = [i for i, ln in enumerate(self.lines) if ln.strip(WSP).startswith("|")]
        self.header, self.align, self.data = tbl[0], tbl[1], tbl[2:]
        self.table = set(tbl)

    def body(self, i):
        """Line `i` without its terminator, byte for byte."""
        return _body(self.lines[i])

    def set_body(self, i, body):
        self.lines[i] = body + _eol(self.lines[i])

    def table_lines(self):
        return [self.header, self.align, *self.data]

    def file_eol(self):
        """CRLF if any line of the file ends in one, else LF: the ending a line
        takes when the line before it has none, as `rowspec add-row` gave it."""
        return "\r\n" if any(ln.endswith("\r\n") for ln in self.lines) else "\n"

    def column(self, name):
        name = _nfc(name)
        if name not in self.cols:
            raise EditRefused("no-such-column", f"no column {name!r}")
        return self.cols.index(name)

    def row(self, rid):
        if self.key is None:
            raise EditRefused("no-key", "the table declares no `key`, so rows have no id")
        k = self.cols.index(self.key)
        for i in self.data:
            if _nfc(split_row(self.lines[i])[k]) == _nfc(rid):
                return i
        raise EditRefused("no-such-row", f"no row with {self.key}={rid!r}")

    def declarations(self):
        """{name: line index} for every declaration line."""
        out = {}
        for i in range(len(self.lines)):
            if i in self.table:
                continue
            d = _declaration(self.body(i))
            if d:
                out[d[0]] = i
        return out

    def refs(self):
        """[(where, line, start, end, name, operand)] for every column name that
        a formula or a declaration mentions. `start` and `end` are offsets in
        that line's body after NFC, which is how a line is written when an edit
        changes it (§3)."""
        out = []
        body = _nfc(self.body(self.header))
        for (a, b), col in zip(_spans(body), self.cols, strict=True):
            inner = body[a:b]
            if "=" in inner:
                base = a + inner.index("=") + 1
                for s, e, name, operand in _formula_refs(body[base:b]):
                    out.append((col, self.header, base + s, base + e, _nfc(name), operand))
        for name, i in self.declarations().items():
            for s, e, ref, operand in _declaration(_nfc(self.body(i)))[3]:
                out.append((f"{name} :=", i, s, e, _nfc(ref), operand))
        return out

    def layout(self):
        """(widths, aligns) when the table is padded to one width per column,
        else None. A new line is padded only in a table that already is."""
        spans = [_spans(self.body(i)) for i in self.table_lines()]
        widths = [b - a for a, b in spans[0]]
        if any([b - a for a, b in s] != widths for s in spans):
            return None
        if not any(
            _padded(self.body(i)[a:b])
            for i, s in zip(self.table_lines(), spans, strict=True)
            for a, b in s
        ):
            return None
        body = self.body(self.align)
        return widths, [_align_kind(body[a:b]) for a, b in spans[1]]

    def insert(self, at, body, eol=None):
        """Insert a line before index `at`, ending in `eol` or as the line before
        it does. A last line with no terminator gains one, and the new line goes
        without, so the file still ends as it did."""
        prev = self.lines[at - 1]
        eol = eol or _eol(prev) or self.file_eol()
        if at == len(self.lines) and not _eol(prev):
            self.lines[at - 1] = prev + eol
            self.lines.insert(at, body)
        else:
            self.lines.insert(at, body + eol)
        self.index()

    def remove(self, i):
        """Remove line `i` and return it. Removing the last line, when it has no
        terminator, takes the terminator off the line before it, so the file
        still ends as it did (§4.1.1) -- unless that line is blank, since a
        blank line without its terminator is no line at all. It is then kept
        whole, and the file ends in its terminator."""
        line = self.lines.pop(i)
        if i == len(self.lines) and not _eol(line) and _body(self.lines[-1]):
            self.lines[-1] = _body(self.lines[-1])
        return line

    def keys(self):
        """The row ids, in file order."""
        k = self.cols.index(self.key)
        return [_nfc(split_row(self.lines[i])[k]) for i in self.data]

    def result(self):
        text = "".join(self.lines)
        evaluate(text)
        return text


def _row_position(d, after, before):
    """The line index a row goes at: after or before a key, else after the last
    row."""
    if after is not None and before is not None:
        raise EditRefused("bad-position", "give after= or before=, not both")
    if after is not None:
        return d.row(after) + 1
    if before is not None:
        return d.row(before)
    return max(d.table_lines()) + 1


def _row_body(d, cells, like):
    """A new table line holding `cells`, indented as line `like` is."""
    body = d.body(like)
    indent = body[: len(body) - len(body.lstrip(WSP))]
    lay = d.layout()
    if lay:
        inner = [_pad(escape_cell(c), w, al) for c, w, al in zip(cells, *lay, strict=True)]
    else:
        inner = [f" {escape_cell(c)} " for c in cells]
    return indent + "|" + "|".join(inner) + "|"


def _sorted_position(d, rid):
    """Where a row keyed `rid` sorts, by code point, in a table whose rows are
    already in key order; otherwise after the last row. A convention for the
    diff, not a rule of the format: a generated id is random, so two rows
    added on two branches land in different gaps instead of both at the end,
    where they always conflict."""
    if d.key is None:
        return max(d.table_lines()) + 1
    keys = d.keys()
    if keys != sorted(keys):
        return max(d.table_lines()) + 1
    later = [i for i, k in zip(d.data, keys, strict=True) if k > rid]
    return later[0] if later else max(d.table_lines()) + 1


def insert_row(text, values=None, *, id=None, after=None, before=None, end=False):
    """Insert one row, after or before the row keyed `after`/`before`, or after
    the last row when `end` is true. With none of the three, the row goes where
    its key sorts if the rows are already in key order, and after the last row
    otherwise. `values` maps column names to cell text; a stored column it
    omits is blank. The row's id is `id`, or the key column's entry in
    `values`, or a generated `r_` and six hex digits. Returns (text, id), and
    id is None for a table with no key.

    The diff is one added line."""
    d = _Doc(text)
    vals = {}
    for c, v in (values or {}).items():
        c = _nfc(c)
        d.column(c)
        vals[c] = _cell_value(v, f"value for {c!r}")
        if c in d.formulas and vals[c] != "":
            raise Malformed(
                f"{c!r} is a computed column; its cells are empty (§5)",
                refusal="value-in-computed-cell",
            )
    if d.key is None:
        if id is not None:
            raise EditRefused("no-key", "the table declares no `key`, so a row has no id")
    elif d.key in vals:
        if id is not None and _nfc(id) != vals[d.key]:
            raise EditRefused("conflicting-id", f"two ids given: {id!r} and {vals[d.key]!r}")
        id = vals[d.key]
    elif id is not None:
        id = _cell_value(id, "id")
    else:
        taken = {_nfc(split_row(d.lines[i])[d.cols.index(d.key)]) for i in d.data}
        id = "r_" + secrets.token_hex(3)
        while id in taken:
            id = "r_" + secrets.token_hex(3)
    if d.key is not None:
        vals[d.key] = id
    cells = [vals.get(c, "") for c in d.cols]
    if end and (after is not None or before is not None):
        raise EditRefused("bad-position", "give one of after=, before= and end=")
    if end or after is not None or before is not None:
        at = _row_position(d, after, before)
    else:
        at = _sorted_position(d, id)
    d.insert(at, _row_body(d, cells, at - 1))
    out = d.result()
    got = split_row(d.lines[at])
    if got != cells:
        raise EditRefused("not-representable", f"the row would read back as {got!r}")
    return out, id


def delete_row(text, id):
    """Delete the row keyed `id`. The diff is one removed line."""
    d = _Doc(text)
    d.remove(d.row(id))
    return d.result()


def add_column(
    text, name, *, formula=None, value="", values=None, after=None, before=None, align="---"
):
    """Add a column after or before the column `after`/`before`, or last. A
    stored column's cells hold `value`, or `values[id]` for the row keyed `id`;
    a computed column (`formula` given) has empty cells. `align` is the new
    alignment cell.

    The diff is every table line: §9.6 gives each row the header's field
    count, so no writer can add a column in fewer."""
    d = _Doc(text)
    name = _nfc(name)
    _check_ident(name, "column name")
    align = _text_value(align, "alignment cell").strip(WSP)
    value = _cell_value(value, "value")
    per_row = {}
    for rid, v in (values or {}).items():
        per_row[d.row(rid)] = _cell_value(v, f"value for row {rid!r}")
    if formula is not None:
        formula = _text_value(formula, "formula").strip(WSP)
        if value != "" or per_row:
            raise Malformed(
                f"{name!r} is a computed column; its cells are empty (§5)",
                refusal="value-in-computed-cell",
            )
        head = f"{name} = {formula}"
    else:
        head = name
    if after is not None and before is not None:
        raise EditRefused("bad-position", "give after= or before=, not both")
    if after is not None:
        k = d.column(after) + 1
    else:
        k = d.column(before) if before is not None else len(d.cols)
    cells = {d.header: head, d.align: align}
    for i in d.data:
        cells[i] = per_row.get(i, value)
    lay = d.layout()
    if lay:
        width = max(len(escape_cell(c)) for c in cells.values()) + 2
        left, right = align.startswith(":"), align.endswith(":") and len(align) > 1
        cells[d.align] = ":" * left + "-" * (width - 2 - left - right) + ":" * right
        kind = _align_kind(align)
    for i, cell in cells.items():
        body = d.body(i)
        spans = _spans(body)
        inner = _pad(escape_cell(cell), width, kind) if lay else f" {escape_cell(cell)} "
        if k < len(spans):
            d.set_body(i, _replace(body, [(spans[k][0], spans[k][0], inner + "|")]))
        else:
            end = spans[-1][1]
            d.set_body(i, _replace(body, [(end, end, "|" + inner)]))
    out = d.result()
    cols, formulas, _r, _d, _o, _k = parse(out)
    if cols[k] != name or formulas.get(name) != (_nfc(formula) if formula is not None else None):
        raise EditRefused("not-representable", f"the header would read back as {cols!r}")
    return out


def delete_column(text, name):
    """Delete a column that no formula or declaration names. The diff is every
    table line, as for `add_column`."""
    d = _Doc(text)
    k = d.column(name)
    name = d.cols[k]
    if len(d.cols) == 1:
        raise EditRefused("last-column", f"{name!r} is the table's only column")
    users = sorted({w for w, _i, _a, _b, ref, _o in d.refs() if ref == name and w != name})
    if users:
        raise EditRefused(
            "column-referenced",
            f"column {name!r} is named by {', '.join(users)}; change or delete those first",
        )
    for i in d.table_lines():
        body = d.body(i)
        spans = _spans(body)
        if k < len(spans) - 1:
            cut = (spans[k][0], spans[k + 1][0], "")
        else:
            cut = (spans[k][0] - 1, spans[k][1], "")
        d.set_body(i, _replace(body, [cut]))
    return d.result()


def _values_under(text, old, new):
    """The evaluated table, with column `old` read as `new`, and every computed
    `#REF!` read as one value. The check is that a rename changes no number:
    §8 reports, among an aggregate's errors, the name that sorts first, so a
    rename can change which error is reported, and the spelling cannot tell a
    shape from a name, since `cycle`, `empty` and `overflow` are column names
    too (§8). A stored cell spelled like an error is text, and stays itself."""
    seq, aggs = evaluate(text)

    def v(x):
        return "#REF!" if type(x) is str and x.startswith("#REF!(") else x

    rows = [{(new if c == old else c): v(x) for c, x in r.items()} for r in seq]
    return rows, {k: v(x) for k, x in aggs.items()}


def rename_column(text, old, new):
    """Rename a column in the header, in every formula and in every declaration
    that names it, and nowhere else: not in a string literal, a function name,
    a numeric literal or an annotation. The diff is the header line and each
    declaration line that names the column."""
    d = _Doc(text)
    k = d.column(old)
    old, new = d.cols[k], _nfc(new)
    _check_ident(new, "column name")
    if new == old:
        return text
    if new in d.cols:
        raise Malformed(f"there is already a column {new!r}", refusal="duplicate-column")
    refs = d.refs()
    users = sorted({w for w, _i, _a, _b, ref, _o in refs if ref == new})
    if users:
        raise EditRefused(
            "rename-captures-reference",
            f"{new!r} is already named by {', '.join(users)}, which would then read "
            f"column {new!r} instead of what it reads now",
        )
    if _LITERAL.match(new):
        users = sorted({w for w, _i, _a, _b, ref, op in refs if ref == old and op})
        if users:
            raise EditRefused(
                "rename-changes-values",
                f"{new!r} is read as a number where {', '.join(users)} names {old!r} (§4.2 rule 7)",
            )
    edits = {}
    for _w, i, a, b, ref, _o in refs:
        if ref == old:
            edits.setdefault(i, []).append((a, b, new))
    # The spans in `refs` are offsets into the NFC form of each line, so a
    # line this edit changes is written in NFC (§3).
    header = _nfc(d.body(d.header))
    spans = _spans(header)
    hedits = edits.pop(d.header, [])
    cells = []
    for (a, b), col in zip(spans, d.cols, strict=True):
        inner = header[a:b]
        mine = [(s - a, e - a, t) for s, e, t in hedits if a <= s < b]
        if col == old:
            pre = inner.split("=", 1)[0]
            s = len(pre) - len(pre.lstrip(WSP))
            mine.append((s, s + len(pre.strip(WSP)), new))
        if mine:
            content = _replace(inner, mine).strip(WSP)
            cells.append((a, b, _refill(inner, content)))
    d.set_body(d.header, _replace(header, cells))
    for i, es in edits.items():
        d.set_body(i, _replace(_nfc(d.body(i)), es))
    out = d.result()
    # Every reference reads what it read before, under the new name, and every
    # value is what it was. Neither should be reachable; a gap above is then a
    # refusal rather than a wrong file.
    want = sorted((new if w == old else w, new if r == old else r) for w, *_x, r, _o in refs)
    got = sorted((w, r) for w, *_x, r, _o in _Doc(out).refs())
    if got != want or _values_under(text, old, new) != _values_under(out, new, new):
        raise EditRefused("rename-changes-values", f"renaming {old!r} would change a value")
    return out


def set_formula(text, column, formula):
    """Replace a computed column's formula. The diff is the header line."""
    d = _Doc(text)
    k = d.column(column)
    column = d.cols[k]
    if column not in d.formulas:
        raise EditRefused(
            "stored-column",
            f"{column!r} is a stored column; giving it a formula would empty every cell",
        )
    formula = _text_value(formula, "formula").strip(WSP)
    body = d.body(d.header)
    a, b = _spans(body)[k]
    inner = body[a:b]
    eq = a + inner.index("=") + 1
    d.set_body(d.header, _replace(body, [(eq, b, _refill(body[eq:b], escape_cell(formula)))]))
    out = d.result()
    if parse(out)[1].get(column) != formula:
        raise EditRefused("not-representable", f"the formula would not read back as {formula!r}")
    return out


def set_declaration(text, name, rhs):
    """Set `name := rhs`: in place, keeping the line's spacing and annotation,
    when the name is declared, and otherwise after the last declaration. `key`
    and `order` are names like any other here. The diff is one line."""
    d = _Doc(text)
    name = _nfc(name)
    _check_ident(name, "declaration name")
    rhs = _text_value(rhs, "declaration").strip(WSP)
    if _strip_annotation(f"{name} := {rhs}") != f"{name} := {rhs}":
        raise EditRefused("not-representable", f"{rhs!r} would be cut at an annotation")
    decls = d.declarations()
    if name in decls:
        i = decls[name]
        _n, a, b, _r = _declaration(d.body(i))
        d.set_body(i, _replace(d.body(i), [(a, b, rhs)]))
    else:
        line = f"{name} := {rhs}"
        if decls:
            d.insert(max(decls.values()) + 1, line)
        else:
            if d.lines[-1].strip(WSP + "\r\n"):
                d.insert(len(d.lines), "")
            d.insert(len(d.lines), line)
        i = d.declarations()[name]
    out = d.result()
    _n, a, b, _r = _declaration(d.body(i))
    if d.body(i)[a:b] != rhs:
        raise EditRefused("not-representable", f"the declaration would not read back as {rhs!r}")
    return out


def delete_declaration(text, name):
    """Delete the declaration of `name`. The diff is one removed line."""
    d = _Doc(text)
    decls = d.declarations()
    if _nfc(name) not in decls:
        raise EditRefused("no-such-declaration", f"nothing declares {name!r}")
    d.remove(decls[_nfc(name)])
    return d.result()


__all__ = [
    "EditRefused",
    "add_column",
    "delete_column",
    "delete_declaration",
    "delete_row",
    "insert_row",
    "rename_column",
    "set_declaration",
    "set_formula",
]
