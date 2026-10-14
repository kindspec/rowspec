# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The exporter, exercised only where its optional extra is installed.

`just test` runs with the extra ABSENT, because that is what `pip install
rowspec` produces and it is the configuration CI has to cover. These tests skip
there. A test that only ever skips is a check that cannot fail, so `just
test-xlsx` and the `xlsx-extra` CI job set `ROWSPEC_REQUIRE_XLSX=1` and the
import below stops being forgiving.

What is asserted here is the workbook's SHAPE: stored values reach the cells,
computed columns and aggregates arrive as formulas over structured references,
no formula holds a coordinate, and what a spreadsheet cannot say is refused.
Nothing here computes a formula, so nothing here claims what one evaluates to;
whether LibreOffice recalculates them to `rowspec eval`'s values is
kindspec/rowspec#36.
"""

import os
import re
import subprocess
import sys
import zipfile

import pytest

if os.environ.get("ROWSPEC_REQUIRE_XLSX") == "1":
    try:
        import openpyxl
    except ModuleNotFoundError as exc:  # a skip here would be a check that cannot fail
        raise RuntimeError(
            "ROWSPEC_REQUIRE_XLSX=1 says these tests must RUN, and openpyxl is not "
            "installed, so they would have skipped instead — which is how a suite "
            "comes to report a pass over an exporter nothing executed. "
            "Run `just test-xlsx`, which installs the extra."
        ) from exc
else:
    openpyxl = pytest.importorskip("openpyxl")

from rowspec.table import Malformed  # noqa: E402
from rowspec_xlsx import NotExpressible, export_file, to_workbook  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TABLE = (
    "| id | item | qty | unit | total = qty * unit |\n"
    "| --- | --- | --: | --: | --: |\n"
    "| r_01 | widget | 10 | 12.00 |  |\n"
    "| r_02 | gadget | 3 | 4.50 |  |\n"
    "\n"
    "key := id\n"
    "grand := sum(total)\n"
)


def sheet(path):
    """Reload from disk. Cell TYPE is part of what is asserted here, and it is
    only real once the file has been written and read back."""
    wb = openpyxl.load_workbook(path)
    return wb[wb.sheetnames[0]]


def grid(path):
    return [list(r) for r in sheet(path).iter_rows(values_only=True)]


def test_the_header_and_the_stored_cells_arrive(tmp_path):
    src = tmp_path / "t.mdtbl"
    src.write_text(TABLE)
    rows = grid(export_file(str(src), str(tmp_path / "t.xlsx")))
    assert rows[0] == ["id", "item", "qty", "unit", "total"]
    assert rows[1][:4] == ["r_01", "widget", 10, 12.0]


GUARDED = "IF(ISNUMBER(rowspec[[#This Row],[{0}]]),rowspec[[#This Row],[{0}]],NA())"


def test_a_computed_column_arrives_as_a_structured_reference_formula(tmp_path):
    """Every operand is guarded, because a spreadsheet reads a blank as `0` and
    §8 reads it as `#REF!` -- the guard is what keeps the formula this format's."""
    src = tmp_path / "t.mdtbl"
    src.write_text(TABLE)
    path = export_file(str(src), str(tmp_path / "t.xlsx"))
    ws = sheet(path)
    want = "(" + GUARDED.format("qty") + "*" + GUARDED.format("unit") + ")"
    assert [ws.cell(r, 5).value for r in (2, 3)] == ["=" + want] * 2
    table = ws.tables["rowspec"]
    assert table.ref == "A1:E3"
    assert [c.name for c in table.tableColumns] == ["id", "item", "qty", "unit", "total"]
    assert table.tableColumns[4].calculatedColumnFormula.attr_text == want


def test_a_declared_aggregate_arrives_below_the_grid_as_subtotal(tmp_path):
    src = tmp_path / "t.mdtbl"
    src.write_text(TABLE)
    ws = sheet(export_file(str(src), str(tmp_path / "t.xlsx")))
    assert ws.cell(ws.max_row, 1).value == "grand"
    assert ws.cell(ws.max_row, 2).value == (
        "=IF(SUBTOTAL(103,rowspec[total])<>SUBTOTAL(102,rowspec[total]),"
        "NA(),SUBTOTAL(109,rowspec[total]))"
    )


def test_a_broken_total_arrives_as_a_formula_not_a_value(tmp_path):
    """§8's `#REF!` must not land in a spreadsheet as a number or a blank.

    A division by zero is decided by the data, so it arrives as the formula
    that will divide by zero. A name the header does not have is decided by the
    header, so that column arrives as an error outright -- a structured
    reference to an absent column is not a formula a spreadsheet will open.
    What either one evaluates to is asserted against LibreOffice (#36).
    """
    src = tmp_path / "t.mdtbl"
    src.write_text(
        "| id | a | z | t = a / z | u = nope + a |\n| -- | -: | -: | -: | -: |\n"
        "| r_1 | 5 | 0 |  |  |\n\nkey := id\n"
    )
    ws = sheet(export_file(str(src), str(tmp_path / "t.xlsx")))
    assert ws.cell(2, 4).value == "=(" + GUARDED.format("a") + "/" + GUARDED.format("z") + ")"
    assert ws.cell(2, 5).value == "=NA()"


# An A1 or R1C1 reference: column letters then a row number, or R<n>C<n>.
COORDINATE = re.compile(
    r"(?<![A-Za-z0-9_.])\$?[A-Za-z]{1,3}\$?[0-9]+(?![A-Za-z0-9_(])|\bR[0-9]*C[0-9]*\b"
)


def formulas_in(path):
    """Every formula in the saved file, read from the XML rather than through
    openpyxl, so a formula openpyxl would not surface is still checked."""
    out = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name.startswith(("xl/worksheets/", "xl/tables/")):
                xml = z.read(name).decode()
                out += re.findall(r"<f>(.*?)</f>", xml)
                out += re.findall(r"<calculatedColumnFormula>(.*?)</calculatedColumnFormula>", xml)
    return out


def test_no_formula_holds_a_coordinate(tmp_path):
    """#35: a coordinate anywhere in a formula is a bug.

    String literals and structured-reference brackets are removed first, so a
    column named `a1` or a literal `"B2"` is not mistaken for a coordinate.
    """
    src = tmp_path / "t.mdtbl"
    src.write_text(
        '| id | a1 | b | c = if(b > 1, a1 * 2, -b) | d = if(id <> "B2", c / 3, 0) |\n'
        "| -- | -: | -: | -: | -: |\n| r_1 | 5 | 2 |  |  |\n\nkey := id\n"
        "s := sum(c)\nn := count(d)\nlo := min(a1)\nhi := max(b)\nm := avg(c)\n"
    )
    found = formulas_in(export_file(str(src), str(tmp_path / "t.xlsx")))
    assert len(found) == 2 * 2 + 5, found  # two columns, cell and table, and five aggregates
    for f in found:
        bare = re.sub(r"\[[^\[\]]*\]", "", re.sub(r"\[[^\[\]]*\]", "", re.sub(r'"[^"]*"', "", f)))
        assert not COORDINATE.search(bare), f"coordinate in {f!r}"


def test_the_coordinate_check_can_fail():
    assert COORDINATE.search("SUM(A1:B2)")
    assert COORDINATE.search("$C$3*2")
    assert COORDINATE.search("R1C1")
    assert not COORDINATE.search("SUBTOTAL(109,rowspec)")


@pytest.mark.parametrize(
    ("table", "why"),
    [
        (
            "| id | d | a | c = cumulative(a) |\n| - | - | - | - |\n| r_1 | 1 | 2 |  |\n\n"
            "key := id\norder := by(d)\n",
            "preceding row",
        ),
        (
            "| id | g | a | t = sum(a where g = @g) |\n| - | - | - | - |\n| r_1 | x | 2 |  |\n\n"
            "key := id\n",
            "where",
        ),
        (
            "| id | g | a |\n| - | - | - |\n| r_1 | x | 2 |\n\n"
            'key := id\ns := sum(a where g = "x")\n',
            "where",
        ),
        (
            '| id | q | t = if(q = "3", 1, 0) |\n| - | - | - |\n| r_1 | 3.0 |  |\n\nkey := id\n',
            "spelling",
        ),
        ("| id | ab | AB |\n| - | - | - |\n| r_1 | 1 | 2 |\n\nkey := id\n", "case"),
        ("| id | a |\n| - | - |\n\nkey := id\n", "no rows"),
        (
            "| id | a | t = a * 1.23456789012345678 |\n| - | - | - |\n| r_1 | 1 |  |\n\n"
            "key := id\n",
            "significant digits",
        ),
    ],
    ids=[
        "row-relative",
        "group-where",
        "declaration-where",
        "text-vs-number",
        "case",
        "empty",
        "literal",
    ],
)
def test_what_a_spreadsheet_cannot_say_is_refused(table, why):
    with pytest.raises(NotExpressible, match=why):
        to_workbook(table)


def test_a_blank_test_on_a_number_column_is_exported(tmp_path):
    """`if(x = "", ...)` reads no spelling, so a number column is fine there:
    a number is never the empty string, to this format or to a spreadsheet."""
    wb = to_workbook(
        '| id | q | t = if(q = "", 0, q) |\n| - | - | - |\n'
        "| r_1 | 3.0 |  |\n| r_2 |  |  |\n\nkey := id\n"
    )
    assert wb.active.cell(2, 3).value.startswith('=IF(EXACT(rowspec[[#This Row],[q]],""),0,')


def test_a_stored_cell_beginning_with_equals_is_not_a_live_formula(tmp_path):
    """§5 makes a stored cell text. openpyxl reads a leading `=` as a formula.

    Exported without forcing the type, this cell arrives as `data_type == "f"`
    and survives save and reload as one — a computed cell the file never had,
    a `=A1` would smuggle a COORDINATE into the output, and a `.mdtbl` is a
    file anyone can open a pull request against.

    Asserted after a save and reload, not on the in-memory workbook, because
    the round trip is where the claim has to hold.
    """
    src = tmp_path / "t.mdtbl"
    src.write_text("| id | note |\n| --- | --- |\n| r_1 | =1+1 |\n\nkey := id\n")
    ws = sheet(export_file(str(src), str(tmp_path / "t.xlsx")))
    assert ws.cell(2, 2).value == "=1+1"
    assert ws.cell(2, 2).data_type == "s", "a stored cell was exported as a live formula"


def test_two_keys_that_differ_only_as_text_stay_two_rows(tmp_path):
    """§9.16 makes a key an identifier, not a number, and §4.2 rule 6 compares
    identifiers as text. `007` and `7` are two rows — §9.5 would refuse them if
    they were one — so an export that coerces the key column merges two row
    identities into one, in the export of a format named after the row id.

    §4.1.6 admits `007` at all precisely so zero-padded identifiers survive.
    """
    src = tmp_path / "t.mdtbl"
    src.write_text("| id | n |\n| --- | --: |\n| 007 | 1 |\n| 7 | 2 |\n\nkey := id\n")
    ws = sheet(export_file(str(src), str(tmp_path / "t.xlsx")))
    keys = [ws.cell(r, 1).value for r in (2, 3)]
    assert keys == ["007", "7"], keys
    assert [ws.cell(r, 1).data_type for r in (2, 3)] == ["s", "s"]
    # The VALUE column keeps the number policy: this is about the key alone.
    assert [ws.cell(r, 2).value for r in (2, 3)] == [1, 2]


def test_a_blank_stored_cell_arrives_as_a_cell_that_is_not_there(tmp_path):
    """`evaluate` returns a blank cell as `""`, which must not become `"None"`,
    `0`, or an EMPTY STRING cell.

    `data_type` is the assertion, not `value`, and that is the whole point of
    this test. Writing `""` emits `<c r="B2" t="inlineStr"/>` — a cell that
    exists and holds empty text, for which `ISBLANK()` is FALSE — while
    writing `None` emits no cell element at all. Measured on the saved
    sheet XML. openpyxl's reader returns `value is None` for BOTH, so a test
    asserting on the value passes over either and this one would be measuring
    nothing: `data_type` is `"n"` for the absent cell and `"inlineStr"` for the
    empty-string one.
    """
    src = tmp_path / "t.mdtbl"
    src.write_text("| id | note |\n| --- | --- |\n| r_1 |  |\n\nkey := id\n")
    ws = sheet(export_file(str(src), str(tmp_path / "t.xlsx")))
    assert ws.cell(2, 2).value is None
    assert ws.cell(2, 2).data_type == "n", "a blank cell was exported as empty TEXT"


def test_a_refused_table_is_refused_here_too(tmp_path):
    """Export defers to the parser rather than writing whatever it can."""
    with pytest.raises(Malformed):
        to_workbook("| id | n |\n| --- | --- |\n| r_01 | 1 |\n| r_01 | 2 |\n\nkey := id\n")


def test_the_module_entry_point_writes_a_file(tmp_path):
    dst = tmp_path / "parts.xlsx"
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([f"{ROOT}/export", f"{ROOT}/reference"]))
    r = subprocess.run(
        [sys.executable, "-m", "rowspec_xlsx", f"{ROOT}/docs/example/parts.mdtbl", str(dst)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert grid(str(dst))[0][0] == "id"


def test_the_module_entry_point_refuses_what_it_cannot_say(tmp_path):
    src = tmp_path / "t.mdtbl"
    src.write_text("| id | ab | AB |\n| - | - | - |\n| r_1 | 1 | 2 |\n\nkey := id\n")
    dst = tmp_path / "t.xlsx"
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([f"{ROOT}/export", f"{ROOT}/reference"]))
    r = subprocess.run(
        [sys.executable, "-m", "rowspec_xlsx", str(src), str(dst)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 1, r.stdout + r.stderr
    assert "not exported" in r.stderr and "case" in r.stderr
    assert not dst.exists(), "a refused export wrote a file"
