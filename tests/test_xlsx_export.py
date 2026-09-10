"""The exporter, exercised only where its optional extra is installed.

`just test` runs with the extra ABSENT, because that is what `pip install
rowspec` produces and it is the configuration CI has to cover. These tests skip
there. A test that only ever skips is a check that cannot fail, so `just
test-xlsx` and the `xlsx-extra` CI job set `ROWSPEC_REQUIRE_XLSX=1` and the
import below stops being forgiving.

What is asserted here is small on purpose: values reach the cells. Whether
LibreOffice recalculates a live workbook is kindspec/rowspec#36 and is not
claimed by anything in this file.
"""

import os
import subprocess
import sys

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
from rowspec_xlsx import export_file, to_workbook  # noqa: E402

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


def test_a_computed_column_arrives_as_its_value(tmp_path):
    src = tmp_path / "t.mdtbl"
    src.write_text(TABLE)
    rows = grid(export_file(str(src), str(tmp_path / "t.xlsx")))
    assert [r[4] for r in rows[1:3]] == [120.0, 13.5]


def test_a_declared_aggregate_arrives_below_the_grid(tmp_path):
    src = tmp_path / "t.mdtbl"
    src.write_text(TABLE)
    rows = grid(export_file(str(src), str(tmp_path / "t.xlsx")))
    assert ["grand", 133.5] == rows[-1][:2]


def test_a_broken_total_arrives_visibly_broken(tmp_path):
    """§8's `#REF!(name)` must not land in a spreadsheet as a number or a blank."""
    src = tmp_path / "t.mdtbl"
    src.write_text(
        "| id | a | z | t = a / z |\n| -- | -: | -: | -: |\n| r_1 | 5 | 0 |  |\n\nkey := id\n"
    )
    rows = grid(export_file(str(src), str(tmp_path / "t.xlsx")))
    assert str(rows[1][3]).startswith("#REF!")


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
