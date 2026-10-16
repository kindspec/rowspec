# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`rowspec.edit`: each operation changes only the lines it is about, keeps
every other byte, and refuses what SPEC.md refuses before returning anything.

The diff shape is the property under test, because the diff is what git
merges: docs/editing-api.md has the rules. `test_edit_merge.py` runs the
operations through real merges.
"""

import difflib
import os
import re
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import Malformed, edit, evaluate, parse  # noqa: E402
from rowspec.table import split_lines  # noqa: E402

BASE = (
    "# parts on hand\n"
    "| id | item | region | qty | unit | total = qty * unit |\n"
    "| --- | --- | --- | --: | --: | --: |\n"
    "| r_01 | widget | EU | 10 | 12.00 |  |\n"
    "| r_02 | gadget | US | 3 | 4.50 |  |\n"
    "| r_03 | bolt | EU | 100 | 0.10 |  |\n"
    "| r_04 | nut | US | 200 | 0.05 |  |\n"
    "\n"
    "key := id\n"
    "grand := sum(total)   # every part\n"
    'eu    := sum(total where region = "EU")\n'
)

PADDED = (
    "| id   | item   | qty | unit  | total = qty * unit |\n"
    "| ---- | ------ | --: | ----: | -----------------: |\n"
    "| r_01 | widget |  10 | 12.00 |                    |\n"
    "| r_02 | gadget |   3 |  4.50 |                    |\n"
    "| r_03 | bolt   | 100 |  0.10 |                    |\n"
    "\n"
    "key := id\n"
    "grand := sum(total)\n"
)


def shape(old, new):
    """(lines removed, lines added) between two texts, terminators included,
    as a line diff counts them: a changed line is one of each."""
    a, b = split_lines(old, keepends=True), split_lines(new, keepends=True)
    removed = added = 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != "equal":
            removed += i2 - i1
            added += j2 - j1
    return removed, added


def values(text):
    seq, aggs = evaluate(text)
    key = parse(text)[5]
    return {r[key]: r for r in seq}, aggs


OPS = {
    "insert_row after": lambda t: edit.insert_row(t, {"item": "cog", "qty": "1"}, after="r_02")[0],
    "insert_row before": lambda t: edit.insert_row(t, {"item": "cog"}, before="r_01")[0],
    "insert_row end": lambda t: edit.insert_row(t, {"item": "cog"}, id="r_09", end=True)[0],
    "insert_row by key": lambda t: edit.insert_row(t, {"item": "cog"}, id="r_015")[0],
    "delete_row": lambda t: edit.delete_row(t, "r_02"),
    "move_row": lambda t: edit.move_row(t, "r_03", before="r_01"),
    "rename_column": lambda t: edit.rename_column(t, "qty", "quantity"),
    "set_formula": lambda t: edit.set_formula(t, "total", "qty * unit * 2"),
    "set_declaration replace": lambda t: edit.set_declaration(t, "grand", "max(total)"),
    "set_declaration new": lambda t: edit.set_declaration(t, "n", "count(id)"),
    "delete_declaration": lambda t: edit.delete_declaration(t, "grand"),
    "add_column": lambda t: edit.add_column(t, "note", after="item"),
    "add_column computed": lambda t: edit.add_column(t, "t2", formula="total * 2"),
    "delete_column": lambda t: edit.delete_column(t, "item"),
}

# (removed, added) for a table of N data rows.
WANT = {
    "insert_row after": lambda n: (0, 1),
    "insert_row before": lambda n: (0, 1),
    "insert_row end": lambda n: (0, 1),
    "insert_row by key": lambda n: (0, 1),
    "delete_row": lambda n: (1, 0),
    "move_row": lambda n: (1, 1),
    "rename_column": lambda n: (1, 1),
    "set_formula": lambda n: (1, 1),
    "set_declaration replace": lambda n: (1, 1),
    "set_declaration new": lambda n: (0, 1),
    "delete_declaration": lambda n: (1, 0),
    "add_column": lambda n: (n + 2, n + 2),
    "add_column computed": lambda n: (n + 2, n + 2),
    "delete_column": lambda n: (n + 2, n + 2),
}

FILES = {"canonical": BASE, "padded": PADDED, "crlf": BASE.replace("\n", "\r\n")}


@pytest.mark.parametrize("op", list(OPS))
@pytest.mark.parametrize("name", list(FILES))
def test_each_operation_changes_only_its_own_lines(op, name):
    src = FILES[name]
    out = OPS[op](src)
    n = len(parse(src)[2])
    assert shape(src, out) == WANT[op](n)


@pytest.mark.parametrize("op", list(OPS))
def test_a_crlf_file_stays_crlf(op):
    src = BASE.replace("\n", "\r\n")
    out = OPS[op](src)
    assert "\n" not in out.replace("\r\n", "")


@pytest.mark.parametrize(
    "src, op",
    [
        (BASE.rstrip("\n"), lambda t: edit.set_declaration(t, "n", "count(id)")),
        ("| a | b |\n| - | - |\n| 1 | 2 |", lambda t: edit.insert_row(t, {"a": "3"})[0]),
    ],
    ids=["declaration", "row"],
)
def test_a_missing_final_terminator_stays_missing(src, op):
    out = op(src)
    assert not out.endswith("\n")
    assert shape(src, out) == (1, 2)  # the old last line gains a terminator


def test_insert_row_writes_the_row_asked_for():
    out, rid = edit.insert_row(BASE, {"item": "a | b", "qty": "5"}, after="r_01")
    assert rid == "r_" + rid[2:] and re.fullmatch(r"r_[0-9a-f]{6}", rid)
    rows, _ = values(out)
    assert rows[rid]["item"] == "a | b" and rows[rid]["qty"] == "5"
    assert rows[rid]["total"] == "#REF!(unit)"
    lines = split_lines(out)
    assert lines[lines.index("| r_01 | widget | EU | 10 | 12.00 |  |") + 1].startswith(f"| {rid} ")


def test_insert_row_takes_the_id_from_values_or_id():
    a, ra = edit.insert_row(BASE, {"id": "r_10", "item": "x"})
    b, rb = edit.insert_row(BASE, {"item": "x"}, id="r_10")
    assert ra == rb == "r_10" and a == b


def test_insert_row_without_a_key_has_no_id():
    src = "| a | b |\n| - | - |\n| 1 | 2 |\n"
    out, rid = edit.insert_row(src, {"a": "3"})
    assert rid is None and out == src + "| 3 |  |\n"


def test_a_padded_table_gets_a_padded_row_and_is_never_reflowed():
    out, _ = edit.insert_row(PADDED, {"item": "cog", "qty": "1", "unit": "2"}, id="r_04")
    assert "| r_04 | cog    |   1 |     2 |                    |\n" in out
    wide, _ = edit.insert_row(PADDED, {"item": "a much longer item"}, id="r_05")
    assert shape(PADDED, wide) == (0, 1)
    assert "| r_05 | a much longer item |     |       |                    |\n" in wide


def test_a_replaced_cell_keeps_its_width_when_it_fits():
    out = edit.rename_column(PADDED, "unit", "cost")
    assert out.splitlines()[0] == "| id   | item   | qty | cost  | total = qty * cost |"
    wide = edit.rename_column(PADDED, "item", "description")
    assert wide.splitlines()[0] == "| id   | description | qty | unit  | total = qty * unit |"


def test_a_padded_table_gets_a_padded_column():
    out = edit.add_column(PADDED, "n", after="id", value="1", align="--:")
    assert out.splitlines()[:3] == [
        "| id   |   n | item   | qty | unit  | total = qty * unit |",
        "| ---- | --: | ------ | --: | ----: | -----------------: |",
        "| r_01 |   1 | widget |  10 | 12.00 |                    |",
    ]


def test_move_row_keeps_the_line_byte_for_byte():
    src = BASE.replace("| r_03 | bolt |", "|  r_03|bolt   |")
    out = edit.move_row(src, "r_03", after="r_04")
    assert out.splitlines()[6] == "|  r_03|bolt   | EU | 100 | 0.10 |  |"
    assert values(out) == values(src)


@pytest.mark.parametrize(
    "header, decls, want_header, want_decls",
    [
        # a string literal, an annotation and a function name are not names
        (
            "| id | qty | sum = qty * 2 |",
            'g := sum(qty where id = "qty")   # qty\n',
            "| id | n | sum = n * 2 |",
            'g := sum(n where id = "qty")   # qty\n',
        ),
        # a column named like a function, read where it is a column
        (
            "| id | sum | x = sum + 1 |",
            "g := sum(sum)\n",
            "| id | n | x = n + 1 |",
            "g := sum(n)\n",
        ),
        # `@` references, a group call and a row-relative call
        (
            "| id | sum | t = sum(sum where id = @id) | p = prior(sum) |",
            "order := by(sum)\n",
            "| id | n | t = sum(n where id = @id) | p = prior(n) |",
            "order := by(n)\n",
        ),
        # a name on either side of a header predicate
        (
            "| id | g | t = count(id where g = @g) |",
            "",
            "| id | n | t = count(id where n = @n) |",
            "",
        ),
        # the left of a comparison is a name even when it looks like a number
        (
            "| id | 2 | x = if(2 > 1, 2, 0) |",
            "",
            "| id | n | x = if(n > 1, 2, 0) |",
            "",
        ),
    ],
)
def test_rename_reaches_every_name_and_nothing_else(header, decls, want_header, want_decls):
    ncols = header.count("|") - 1
    old = header.split("|")[2].strip()
    rows = "| r_1 | 3 |" + "  |" * (ncols - 2) + "\n"
    src = f"{header}\n|{' --- |' * ncols}\n{rows}\nkey := id\n{decls}"
    out = edit.rename_column(src, old, "n")
    assert out == f"{want_header}\n|{' --- |' * ncols}\n{rows}\nkey := id\n{want_decls}"


def test_rename_renames_the_key_and_keeps_every_value():
    out = edit.rename_column(BASE, "id", "code")
    assert "key := code\n" in out
    old_rows, old_aggs = values(BASE)
    new_rows, new_aggs = values(out)
    assert new_aggs == old_aggs
    assert {
        k: {("code" if c == "id" else c): v for c, v in r.items()} for k, r in old_rows.items()
    } == new_rows


def test_set_declaration_keeps_spacing_and_annotation():
    out = edit.set_declaration(BASE, "grand", "max(total)")
    assert "grand := max(total)   # every part\n" in out
    out = edit.set_declaration(BASE, "eu", 'sum(qty where region = "EU")')
    assert 'eu    := sum(qty where region = "EU")\n' in out


def test_a_first_declaration_is_separated_by_a_blank_line():
    src = "| id | a |\n| - | - |\n| r_1 | 1 |\n"
    out = edit.set_declaration(src, "key", "id")
    assert out == src + "\nkey := id\n"
    assert shape(src, out) == (0, 2)


def test_values_are_written_nfc():
    out, _ = edit.insert_row(BASE, {"item": "café"}, id="r_09")
    assert "| r_09 | café |" in out


@pytest.mark.parametrize(
    "call, refusal",
    [
        (lambda: edit.insert_row(BASE, {"item": "x"}, id="r_01"), "duplicate-row-id"),
        (lambda: edit.insert_row(BASE, {"item": "x"}, id="r 9"), "bad-identifier"),
        (lambda: edit.insert_row(BASE, {"total": "5"}), "value-in-computed-cell"),
        (lambda: edit.insert_row(BASE, {"item": "---", "id": "---"}), "bad-identifier"),
        (lambda: edit.add_column(BASE, "qty"), "duplicate-column"),
        (lambda: edit.add_column(BASE, "a b"), "bad-identifier"),
        (lambda: edit.add_column(BASE, "a=b"), "bad-identifier"),
        (lambda: edit.add_column(BASE, "t", formula="qty ^ 2"), "malformed-formula"),
        (lambda: edit.add_column(BASE, "t", formula="1", value="2"), "value-in-computed-cell"),
        (lambda: edit.rename_column(BASE, "qty", "unit"), "duplicate-column"),
        (lambda: edit.rename_column(BASE, "qty", "q-ty"), "bad-identifier"),
        (lambda: edit.set_formula(BASE, "total", "cumulative(qty)"), "rowrel-without-order"),
        (lambda: edit.set_declaration(BASE, "grand", "sum(qty) * 2"), "malformed-declaration"),
        (lambda: edit.set_declaration(BASE, "order", "by(qty)"), None),
        (lambda: edit.set_declaration(BASE, "g", "median(qty)"), "unknown-aggregate"),
        (lambda: edit.delete_declaration(BASE + "order := by(qty)\n", "key"), "order-without-key"),
    ],
)
def test_a_result_spec_refuses_is_refused_with_its_identifier(call, refusal):
    if refusal is None:
        call()  # a valid order: the control for the row above it
        return
    with pytest.raises(Malformed) as e:
        call()
    assert e.value.refusal == refusal


@pytest.mark.parametrize(
    "call, reason",
    [
        (lambda: edit.insert_row(BASE, {"item": "a\nb"}), "line-break"),
        (lambda: edit.insert_row(BASE, {"item": "a\rb"}), "line-break"),
        (lambda: edit.insert_row(BASE, {"item": " a"}), "not-representable"),
        (lambda: edit.insert_row(BASE, {"nope": "a"}), "no-such-column"),
        (lambda: edit.insert_row(BASE, {}, after="r_99"), "no-such-row"),
        (lambda: edit.insert_row(BASE, {}, after="r_01", before="r_02"), "bad-position"),
        (lambda: edit.insert_row("| a |\n| - |\n", {}, id="r_1"), "no-key"),
        (lambda: edit.delete_row(BASE, "r_99"), "no-such-row"),
        (lambda: edit.move_row(BASE, "r_01", after="r_01"), "bad-position"),
        (lambda: edit.insert_row(BASE, {"id": "r_10"}, id="r_11"), "conflicting-id"),
        (lambda: edit.delete_column(BASE, "qty"), "column-referenced"),
        (lambda: edit.delete_column(BASE, "region"), "column-referenced"),
        (lambda: edit.delete_column(BASE, "id"), "column-referenced"),
        (lambda: edit.delete_column("| a |\n| - |\n", "a"), "last-column"),
        (lambda: edit.rename_column(BASE, "nope", "x"), "no-such-column"),
        (
            lambda: edit.rename_column(BASE.replace("qty * unit", "qty * k"), "unit", "k"),
            "rename-captures-reference",
        ),
        (lambda: edit.rename_column(BASE, "qty", "3"), "rename-changes-values"),
        (lambda: edit.set_formula(BASE, "qty", "1"), "stored-column"),
        (lambda: edit.set_formula(BASE, "total", "qty\n* unit"), "line-break"),
        (lambda: edit.set_declaration(BASE, "g", "sum(qty) # x"), "not-representable"),
        (lambda: edit.delete_declaration(BASE, "nope"), "no-such-declaration"),
    ],
)
def test_a_request_that_cannot_be_written_is_refused_with_a_reason(call, reason):
    with pytest.raises(edit.EditRefused) as e:
        call()
    assert e.value.reason == reason


def test_renaming_onto_a_number_says_where_it_would_be_read_as_one():
    with pytest.raises(edit.EditRefused) as e:
        edit.rename_column(BASE, "qty", "3")
    assert "read as a number where total names 'qty'" in str(e.value)


def test_a_refused_input_is_not_edited():
    with pytest.raises(Malformed) as e:
        edit.delete_row(BASE + "key := item\n", "r_01")
    assert e.value.refusal == "duplicate-declaration"


def test_a_column_named_only_by_its_own_formula_can_be_deleted():
    src = "| id | x = x + 1 |\n| - | - |\n| r_1 |  |\n\nkey := id\n"
    assert edit.delete_column(src, "x") == "| id |\n| - |\n| r_1 |\n\nkey := id\n"


def test_moving_a_row_to_the_end_of_a_file_with_no_final_terminator():
    src = BASE.split("\n\n")[0].replace("# parts on hand\n", "key := id\n\n")
    out = edit.move_row(src, "r_01")
    assert out.endswith("| r_01 | widget | EU | 10 | 12.00 |  |")
    assert values(out) == values(src)


def keys_of(text):
    return [r["id"] for r in parse(text)[2]]


def test_a_row_goes_where_its_key_sorts_when_the_rows_are_in_key_order():
    out, _ = edit.insert_row(BASE, {"item": "x"}, id="r_025")
    assert keys_of(out) == ["r_01", "r_02", "r_025", "r_03", "r_04"]
    out, _ = edit.insert_row(BASE, {"item": "x"}, id="r_00")
    assert keys_of(out) == ["r_00", "r_01", "r_02", "r_03", "r_04"]


def test_a_row_goes_last_when_the_rows_are_not_in_key_order():
    src = edit.move_row(BASE, "r_01", after="r_03")
    out, _ = edit.insert_row(src, {"item": "x"}, id="r_025")
    assert keys_of(out) == ["r_02", "r_03", "r_01", "r_04", "r_025"]


def test_end_places_a_row_last_whatever_its_key():
    out, _ = edit.insert_row(BASE, {"item": "x"}, id="r_00", end=True)
    assert keys_of(out)[-1] == "r_00"
    with pytest.raises(edit.EditRefused) as e:
        edit.insert_row(BASE, {"item": "x"}, after="r_01", end=True)
    assert e.value.reason == "bad-position"


UNTERMINATED = "key := id\n\n" + BASE.split("\n\n")[0].replace("# parts on hand\n", "")


@pytest.mark.parametrize(
    "op",
    [
        lambda t: edit.delete_row(t, "r_04"),
        lambda t: edit.move_row(t, "r_04", before="r_01"),
        lambda t: edit.delete_declaration(t + "\ng := sum(qty)", "g"),
    ],
    ids=["delete_row", "move_row", "delete_declaration"],
)
def test_removing_an_unterminated_last_line_keeps_the_file_unterminated(op):
    assert not UNTERMINATED.endswith("\n")
    out = op(UNTERMINATED)
    assert not out.endswith("\n")
    evaluate(out)
