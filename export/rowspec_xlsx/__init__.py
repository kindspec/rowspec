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
structured references, no `SUBTOTAL`, no number formats.

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
    arrives visibly broken rather than as a number or a blank.
    """
    if v is None:
        return None
    if isinstance(v, int | float) and not isinstance(v, bool):
        return v
    try:
        return num(str(v))
    except ValueError:
        return str(v) or None


def to_workbook(text, sheet_title="table"):
    """Build a workbook from `.mdtbl` source. Raises `Malformed` on a bad table."""
    cols = parse(text)[0]
    rows, aggs = evaluate(text)
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title
    ws.append(list(cols))
    for row in rows:
        ws.append([_value(row.get(c)) for c in cols])
    for name, value in aggs.items():
        ws.append([None])  # one blank row between the grid and the aggregates
        ws.append([name, _value(value)])
    return wb


def export_file(src, dst, sheet_title="table"):
    with open(src, encoding="utf-8") as fh:
        wb = to_workbook(fh.read(), sheet_title)
    wb.save(dst)
    return dst
