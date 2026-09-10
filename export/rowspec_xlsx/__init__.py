"""Export a `.mdtbl` to `.xlsx` — deliberately OUTSIDE `reference/`.

`reference/` is standard-library-only because a dependency there is a
dependency every independent implementation inherits, and an independent
implementation of a table format must not be required to read xlsx. So the
exporter lives here, ships as the `rowspec[xlsx]` extra, and the boundary is
held by a test that fails if `reference/` ever imports it — `tests/test_boundary.py`
— rather than by anyone remembering this paragraph.

The direction is one-way on purpose: this package imports `rowspec`, and
nothing in `rowspec` may import this package.

What it writes today is the least interesting workbook that could be correct:
one sheet, the header, every cell as a LITERAL value already computed by
`rowspec.table.evaluate`, and the declared aggregates below the grid. No
structured references, no `SUBTOTAL`, no number formats — so a `1.50` in a
currency column arrives as `1.5` and displays wrong, and `-0` arrives as
`-0.0`. Nothing here is a formula: `_append` forces every string cell to text,
because a stored cell is text under §5 and a spreadsheet application would
otherwise read a leading `=` as a live formula.

That is deliberate. The claim worth making — that a `.mdtbl` arrives as a live
spreadsheet rather than a frozen picture of one — is kindspec/rowspec#35
(structured references and `SUBTOTAL`) and #36 (assert on the values
LibreOffice recalculates, not on the bytes we wrote). Neither is checked here,
so neither is claimed here.
"""

try:
    from openpyxl import Workbook
except ModuleNotFoundError as exc:  # the extra is absent, which is the default
    raise ModuleNotFoundError(
        "xlsx export is an optional extra of rowspec, and it is not installed: "
        "pip install 'rowspec[xlsx]'"
    ) from exc

from rowspec.table import evaluate, num, parse

__all__ = ["export_file", "to_workbook"]


def _value(v):
    """Numbers arrive as numbers, everything else as text, blanks as blank.

    A stored cell matching §4.1's number grammar already IS a number to §8's
    evaluator, so writing it into a spreadsheet as text would contradict the
    format's own reading of the same cell — and text that looks like a number
    is the single most annoying thing to be handed in a workbook.

    `num` rather than `float` on purpose: it is the format's grammar, and it is
    deliberately narrower. `1_000`, `1e3` and Arabic-Indic digits are text
    here, exactly as they are under §8.

    A `#REF!(name)` is a string under §8 and fails `num`, so a broken total
    arrives visibly broken rather than as a number or a blank. A blank cell
    reaches this as `""` and arrives as an empty cell, not as `"None"`.

    This is a VALUE policy and it must not be applied to the key column: §9.16
    makes a key an identifier, not a number. See `to_workbook`.
    """
    if isinstance(v, int | float) and not isinstance(v, bool):
        return v
    try:
        return num(str(v))
    except ValueError:
        return str(v) or None


def _append(ws, values):
    """Append one row, then force every string cell to TEXT.

    openpyxl infers a cell's type from its value, so a stored cell of `=1+1`
    lands as a LIVE FORMULA (`data_type == "f"`) and survives save and reload
    as one. Three things are wrong with that. §5 makes a stored cell text, so
    promoting it to a computed cell is not the file the format describes. A
    `=A1` would put a COORDINATE in the output, which is the one thing this
    format does not have. And a `.mdtbl` is a file anyone can open a pull
    request against, so it is formula injection with a review step in front of
    it.
    """
    ws.append(values)
    for cell in ws[ws.max_row]:
        if isinstance(cell.value, str):
            cell.data_type = "s"


def to_workbook(text, sheet_title="table"):
    """Build a workbook from `.mdtbl` source. Raises `Malformed` on a bad table."""
    cols, _formulas, _rows, _decls, _order, key = parse(text)
    rows, aggs = evaluate(text)
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title
    _append(ws, list(cols))
    for row in rows:
        # The KEY column is exported verbatim, never coerced. §9.16 makes a key
        # an identifier and §4.2 rule 6 compares identifiers as text, so `007`
        # and `7` are two rows -- §9.5 would refuse them if they were one.
        # Coercing them to a number merges two row identities into one, in the
        # export of a format whose whole unit of identity is the row id. §4.1.6
        # admits `007` at all precisely so zero-padded identifiers survive.
        _append(ws, [str(row[c]) if c == key else _value(row[c]) for c in cols])
    for name, value in aggs.items():
        _append(ws, [None])  # one blank row between the grid and the aggregates
        _append(ws, [name, _value(value)])
    return wb


def export_file(src, dst, sheet_title="table"):
    with open(src, encoding="utf-8") as fh:
        wb = to_workbook(fh.read(), sheet_title)
    wb.save(dst)
    return dst
