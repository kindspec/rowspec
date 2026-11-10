# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §6, §9.28, §10 and §13: rows stay in key order (#284)."""

import json
import pathlib
import subprocess
import unicodedata

import pytest
import rowspec
from rowspec import canon, evaluate, set_cell, structure
from rowspec import edit as ed
from rowspec.cli import main
from rowspec.csvmode import check_file
from rowspec.table import Malformed


def table(*keys, tail="\nkey := id\ns := sum(qty)\n"):
    rows = "".join(f"| {k} | {n} |\n" for n, k in enumerate(keys, 1))
    return "| id | qty |\n| --- | --: |\n" + rows + tail


def refusal_of(text):
    with pytest.raises(Malformed) as e:
        evaluate(text)
    return e.value.refusal


# --- the refusal ------------------------------------------------------------


def test_rows_out_of_order_are_refused():
    assert refusal_of(table("r_2", "r_1")) == "rows-out-of-order"


def test_rows_in_order_are_accepted():
    evaluate(table("r_1", "r_2", "r_3"))


def test_keys_compare_by_code_point_not_as_numbers():
    evaluate(table("r_10", "r_9"))
    assert refusal_of(table("r_9", "r_10")) == "rows-out-of-order"


def test_keys_compare_after_nfc():
    nfd = unicodedata.normalize("NFD", "é")
    # NFD `e` + U+0301 sorts before `f`; NFC `é` (U+00E9) sorts after it.
    assert refusal_of(table(nfd, "f")) == "rows-out-of-order"
    evaluate(table("f", nfd))


def test_equal_keys_stay_duplicate_row_id():
    assert refusal_of(table("r_1", "r_1")) == "duplicate-row-id"
    assert refusal_of(table("r_2", "r_1", "r_2")) == "duplicate-row-id"


def test_declaring_an_order_does_not_relax_the_rule():
    text = "| id | day |\n| --- | --: |\n| r_2 | 1 |\n| r_1 | 2 |\n\nkey := id\norder := by(day)\n"
    assert refusal_of(text) == "rows-out-of-order"


def test_a_table_with_no_key_has_no_rule():
    evaluate("| id | qty |\n| --- | --: |\n| b | 1 |\n| a | 2 |\n\ns := sum(qty)\n")


@pytest.mark.parametrize(
    ("tail", "want"),
    [
        ("\nkey := id\ns := median(qty)\n", "unknown-aggregate"),
        ("\nkey := id\norder := by(nope)\n", "bad-order-column"),
    ],
)
def test_any_other_refusal_is_reported_instead(tail, want):
    assert refusal_of(table("r_2", "r_1", tail=tail)) == want


def test_the_message_names_the_rows_and_the_repair():
    with pytest.raises(Malformed) as e:
        evaluate(table("r_2", "r_1"))
    assert "r_1" in str(e.value) and "r_2" in str(e.value)
    assert "rowspec check --fmt --sort-rows" in str(e.value)
    assert "deleted" in str(e.value)


# --- canon and --fmt --------------------------------------------------------


def test_canon_sorts_rows_by_key_moving_each_line_whole():
    assert canon(table("r_2", "r_1")) == (
        "| id | qty |\n| --- | --- |\n| r_1 | 2 |\n| r_2 | 1 |\n\nkey := id\ns := sum(qty)\n"
    ).replace("| --- | --- |", "| --- | --: |")


def test_canon_output_is_valid_and_canon_is_idempotent():
    once = canon(table("r_3", "r_1", "r_2"))
    evaluate(once)
    assert canon(once) == once


def test_canon_leaves_a_table_with_no_key_in_file_order():
    text = "| id | qty |\n| --- | --: |\n| b | 1 |\n| a | 2 |\n\ns := sum(qty)\n"
    assert canon(text) == text


def test_canon_keeps_a_file_with_no_final_terminator_without_one():
    text = "key := id\n\n| id | qty |\n| --- | --: |\n| r_2 | 1 |\n| r_1 | 2 |"
    out = canon(text)
    assert out == "key := id\n\n| id | qty |\n| --- | --: |\n| r_1 | 2 |\n| r_2 | 1 |"
    assert canon(out) == out


def test_canon_does_not_repair_another_refusal():
    with pytest.raises(Malformed) as e:
        canon(table("r_1", "r_1"))
    assert e.value.refusal == "duplicate-row-id"


def test_check_fmt_migrates_a_file_out_of_order(tmp_path, capsys):
    f = tmp_path / "t.mdtbl"
    f.write_text(table("r_2", "r_1"), encoding="utf-8")
    assert main(["check", "--fmt", "--sort-rows", str(f)]) == 0
    assert "reformatted" in capsys.readouterr().out
    evaluate(f.read_text(encoding="utf-8"))


def test_plain_fmt_never_sorts(tmp_path, capsys):
    """§10: after a merge, sorting would make a row another branch deleted
    valid, so a routine format step must not do it unasked."""
    f = tmp_path / "t.mdtbl"
    f.write_text(table("r_2", "r_1"), encoding="utf-8")
    before = f.read_bytes()
    assert main(["check", "--fmt", str(f)]) == 1
    assert "[rows-out-of-order]" in capsys.readouterr().err
    assert f.read_bytes() == before


def test_sort_rows_needs_fmt(tmp_path):
    f = tmp_path / "t.mdtbl"
    f.write_text(table("r_2", "r_1"), encoding="utf-8")
    before = f.read_bytes()
    assert main(["check", "--sort-rows", str(f)]) == 2
    assert f.read_bytes() == before


def test_canon_keeps_a_refusal_only_evaluation_finds():
    with pytest.raises(Malformed) as e:
        canon(table("r_2", "r_1", tail="\nkey := id\ns := median(qty)\n"))
    assert e.value.refusal == "unknown-aggregate"


def test_a_key_write_to_a_taken_key_is_a_duplicate():
    t = table("r_1", "r_2", "r_3")
    with pytest.raises(ed.EditRefused) as e:
        set_cell(structure(t), "r_1", "id", "r_2")
    assert e.value.reason == "duplicate-row-id"


def test_a_position_no_generated_key_can_reach_is_refused_without_naming_one():
    t = "| id | a |\n| --- | --- |\n| zeta | x |\n\nkey := id\n"
    with pytest.raises(ed.EditRefused) as e:
        ed.add_row(t, {"a": "z"}, end=True)
    assert "generated" in str(e.value) and "r_" not in str(e.value)


def test_check_without_fmt_refuses_and_leaves_the_file(tmp_path, capsys):
    f = tmp_path / "t.mdtbl"
    f.write_text(table("r_2", "r_1"), encoding="utf-8")
    before = f.read_bytes()
    assert main(["check", str(f)]) == 1
    assert "[rows-out-of-order]" in capsys.readouterr().err
    assert f.read_bytes() == before


def test_check_fmt_check_reports_it_without_writing(tmp_path):
    f = tmp_path / "t.mdtbl"
    f.write_text(table("r_2", "r_1"), encoding="utf-8")
    before = f.read_bytes()
    assert main(["check", "--fmt-check", str(f)]) == 1
    assert f.read_bytes() == before


def test_check_fmt_leaves_a_file_with_another_refusal(tmp_path, capsys):
    f = tmp_path / "t.mdtbl"
    f.write_text(table("r_2", "r_1", tail="\nkey := id\ns := median(qty)\n"), encoding="utf-8")
    before = f.read_bytes()
    assert main(["check", "--fmt", "--sort-rows", str(f)]) == 1
    assert "[unknown-aggregate]" in capsys.readouterr().err
    assert f.read_bytes() == before


# --- the merge the rule exists for ------------------------------------------


@pytest.mark.parametrize("moved_on", ["ours", "theirs"])
@pytest.mark.parametrize("to", ["top", "end"])
def test_a_row_moved_against_a_delete_is_refused(tmp_path, moved_on, to):
    keys = ["r_1", "r_2", "r_3", "r_4", "r_5", "r_6"]
    gone = "r_3"
    rest = [k for k in keys if k != gone]
    moved = [gone, *rest] if to == "top" else [*rest, gone]
    base = table(*keys)

    def lines(order):
        by = {k: f"| {k} | {keys.index(k) + 1} |\n" for k in keys}
        return table_of(order, by)

    def table_of(order, by):
        return (
            "| id | qty |\n| --- | --: |\n"
            + "".join(by[k] for k in order)
            + ("\nkey := id\ns := sum(qty)\n")
        )

    # A move out of key order is refused on the branch that made it.
    assert refusal_of(lines(moved)) == "rows-out-of-order"

    root = pathlib.Path(tmp_path)
    (root / "base").write_text(base, encoding="utf-8")
    (root / "moved").write_text(lines(moved), encoding="utf-8")
    (root / "deleted").write_text(lines(rest), encoding="utf-8")
    ours, theirs = ("moved", "deleted") if moved_on == "ours" else ("deleted", "moved")
    subprocess.run(
        ["git", "merge-file", str(root / ours), str(root / "base"), str(root / theirs)],
        check=True,
    )
    merged = (root / ours).read_text(encoding="utf-8")
    assert "<<<<<<<" not in merged, "the premise of the issue: stock git reports no conflict"
    assert f"| {gone} |" in merged, "the premise of the issue: the deleted row comes back"
    if to == "top":
        assert refusal_of(merged) == "rows-out-of-order"


# --- the CSV profile --------------------------------------------------------


def csv_refusals(tmp_path, body, sidecar=None):
    p = tmp_path / "data.csv"
    p.write_text(body, encoding="utf-8", newline="")
    if sidecar is not None:
        (tmp_path / "data.csv.rowspec.json").write_text(json.dumps(sidecar), encoding="utf-8")
    return [f.refusal for f in check_file(str(p)) if f.level == "refuse"]


def test_csv_key_only(tmp_path):
    assert csv_refusals(tmp_path, "id,v\nb,1\na,2\n", {"key": "id"}) == ["rows-out-of-order"]


def test_csv_key_only_in_order(tmp_path):
    assert csv_refusals(tmp_path, "id,v\na,1\nb,2\n", {"key": "id"}) == []


def test_csv_no_sidecar_has_no_rule(tmp_path):
    assert csv_refusals(tmp_path, "id,v\nb,1\na,2\n") == []


def test_csv_order_is_by_number_then_key(tmp_path):
    side = {"key": "id", "order": "n"}
    assert csv_refusals(tmp_path, "id,n\nb,2\na,10\n", side) == []
    assert csv_refusals(tmp_path, "id,n\nb,10\na,2\n", side) == ["rows-out-of-order"]


def test_csv_tied_order_values_fall_back_to_the_key(tmp_path):
    side = {"key": "id", "order": "n"}
    assert csv_refusals(tmp_path, "id,n\na,1\nb,1\n", side) == []
    assert csv_refusals(tmp_path, "id,n\nb,1\na,1\n", side) == ["rows-out-of-order"]


def test_csv_dates_order_by_year_month_day(tmp_path):
    side = {"key": "id", "order": "d"}
    assert csv_refusals(tmp_path, "id,d\na,2026-2-1\nb,2026-03-01\n", side) == []
    assert csv_refusals(tmp_path, "id,d\nb,2026-03-01\na,2026-2-1\n", side) == ["rows-out-of-order"]


def test_csv_text_order_is_by_code_point_over_nfc(tmp_path):
    side = {"key": "id", "order": "t"}
    nfd = unicodedata.normalize("NFD", "é")
    assert csv_refusals(tmp_path, f"id,t\na,f\nb,{nfd}\n", side) == []
    assert csv_refusals(tmp_path, f"id,t\nb,{nfd}\na,f\n", side) == ["rows-out-of-order"]


def test_csv_keys_compare_after_nfc(tmp_path):
    nfd = unicodedata.normalize("NFD", "é")
    assert csv_refusals(tmp_path, f"id,v\nf,1\n{nfd},2\n", {"key": "id"}) == []
    assert csv_refusals(tmp_path, f"id,v\n{nfd},1\nf,2\n", {"key": "id"}) == ["rows-out-of-order"]


@pytest.mark.parametrize(
    ("body", "side", "want"),
    [
        ("id,v\nb,1\nb,2\n", {"key": "id"}, ["duplicate-row-id"]),
        ("id,v\nb,1\nb,2\na,3\n", {"key": "id"}, ["duplicate-row-id"]),
        ("id,n\nb,2\na,\n", {"key": "id", "order": "n"}, ["bad-order-column"]),
        ("id,v\nb,1\n​a,2\n", {"key": "id"}, ["bad-identifier"]),
        ("id,v\nb,1\na\n", {"key": "id"}, ["row-field-count"]),
    ],
)
def test_csv_any_other_refusal_is_reported_instead(tmp_path, body, side, want):
    assert csv_refusals(tmp_path, body, side) == want


def test_csv_a_malformed_sidecar_is_reported_instead(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("id,v\nb,1\na,2\n", encoding="utf-8")
    (tmp_path / "data.csv.rowspec.json").write_text("{", encoding="utf-8")
    with pytest.raises(Malformed) as e:
        check_file(str(p))
    assert e.value.refusal == "malformed-declaration"


# --- the editing API --------------------------------------------------------


def test_add_row_goes_where_its_key_sorts():
    out, _ = ed.add_row(table("r_1", "r_3"), {"qty": "9"}, row_key="r_2")
    evaluate(out)
    assert out.index("| r_1 |") < out.index("| r_2 |") < out.index("| r_3 |")


def test_add_row_with_no_key_goes_last():
    text = "| id | qty |\n| --- | --: |\n| b | 1 |\n\ns := sum(qty)\n"
    out, got = ed.add_row(text, {"id": "a", "qty": "2"})
    assert got is None
    assert out.index("| b |") < out.index("| a |")


def test_add_row_position_compares_after_nfc():
    nfd = unicodedata.normalize("NFD", "é")
    out, _ = ed.add_row(table("f", nfd), {"qty": "9"}, row_key="g")
    evaluate(out)
    assert out.index("| f |") < out.index("| g |") < out.index(nfd)


@pytest.mark.parametrize(
    "where",
    [{"after": "r_3"}, {"before": "r_1"}, {"end": True}],
)
def test_a_position_out_of_key_order_is_refused(where):
    with pytest.raises(ed.EditRefused) as e:
        ed.add_row(table("r_1", "r_3"), {"qty": "9"}, row_key="r_2", **where)
    assert e.value.reason == "out-of-key-order"
    assert e.value.refusal is None


@pytest.mark.parametrize(
    "where",
    [{"after": "r_1"}, {"before": "r_3"}],
)
def test_a_position_in_key_order_is_accepted(where):
    out, _ = ed.add_row(table("r_1", "r_3"), {"qty": "9"}, row_key="r_2", **where)
    evaluate(out)


def test_end_is_accepted_for_a_key_that_sorts_last():
    out, _ = ed.add_row(table("r_1", "r_3"), {"qty": "9"}, row_key="r_4", end=True)
    assert out.index("| r_3 |") < out.index("| r_4 |")


def test_a_position_on_a_duplicate_key_stays_duplicate_row_id():
    with pytest.raises(Malformed) as e:
        ed.add_row(table("r_1", "r_3"), {"qty": "9"}, row_key="r_1", before="r_3")
    assert e.value.refusal == "duplicate-row-id"


def test_an_edit_of_a_file_out_of_order_is_refused_as_the_input():
    with pytest.raises(Malformed) as e:
        ed.add_row(table("r_2", "r_1"), {"qty": "9"})
    assert e.value.refusal == "rows-out-of-order"


def test_set_cell_on_the_key_that_keeps_the_order_is_accepted():
    out = ed.set_cell(table("r_1", "r_5"), "r_5", "id", "r_3")
    evaluate(out)


def test_set_cell_on_the_key_that_breaks_the_order_is_refused():
    with pytest.raises(ed.EditRefused) as e:
        ed.set_cell(table("r_1", "r_5"), "r_5", "id", "r_0")
    assert e.value.reason == "out-of-key-order"


def test_set_declaration_key_that_breaks_the_order_is_refused():
    text = "| id | code |\n| --- | --: |\n| r_1 | b |\n| r_2 | a |\n\nkey := id\n"
    with pytest.raises(ed.EditRefused) as e:
        ed.set_declaration(text, "key", "code")
    assert e.value.reason == "out-of-key-order"


def test_structure_set_cell_on_the_key_that_breaks_the_order_is_refused():
    st = structure(table("r_1", "r_5"))
    with pytest.raises(ed.EditRefused) as e:
        set_cell(st, "r_5", "id", "r_0")
    assert e.value.reason == "out-of-key-order"


def test_structure_set_cell_on_the_key_that_keeps_the_order_is_accepted():
    st = structure(table("r_1", "r_5"))
    assert rowspec.render(set_cell(st, "r_5", "id", "r_3")).count("r_3") == 1


def test_a_refused_cli_edit_leaves_the_file(tmp_path, capsys):
    f = tmp_path / "t.mdtbl"
    f.write_text(table("r_1", "r_3"), encoding="utf-8")
    before = f.read_bytes()
    assert main(["add-row", str(f), "9", "--id", "r_2", "--end"]) == 1
    assert "[out-of-key-order]" in capsys.readouterr().err
    assert f.read_bytes() == before


def test_a_generated_key_is_never_refused_for_the_position_it_was_given():
    """`end=True` with no key must draw one that sorts last. A draw that
    ignored the position fails about one call in five here."""
    text = "| id | a |\n| --- | --- |\n| r_3 | x |\n\nkey := id\n"
    for _ in range(300):
        out, key = ed.add_row(text, {"a": "z"}, end=True)
        assert key > "r_3"
        assert out.index("r_3") < out.index(key)
