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


def grid(path):
    wb = openpyxl.load_workbook(path)
    return [list(r) for r in wb[wb.sheetnames[0]].iter_rows(values_only=True)]


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
