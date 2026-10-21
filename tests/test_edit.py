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
import unicodedata

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
    "add_row after": lambda t: edit.add_row(t, {"item": "cog", "qty": "1"}, after="r_02")[0],
    "add_row before": lambda t: edit.add_row(t, {"item": "cog"}, before="r_01")[0],
    "add_row end": lambda t: edit.add_row(t, {"item": "cog"}, row_key="r_09", end=True)[0],
    "add_row by key": lambda t: edit.add_row(t, {"item": "cog"}, row_key="r_015")[0],
    "delete_row": lambda t: edit.delete_row(t, "r_02"),
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
    "add_row after": lambda n: (0, 1),
    "add_row before": lambda n: (0, 1),
    "add_row end": lambda n: (0, 1),
    "add_row by key": lambda n: (0, 1),
    "delete_row": lambda n: (1, 0),
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
        ("| a | b |\n| - | - |\n| 1 | 2 |", lambda t: edit.add_row(t, {"a": "3"})[0]),
    ],
    ids=["declaration", "row"],
)
def test_a_missing_final_terminator_stays_missing(src, op):
    out = op(src)
    assert not out.endswith("\n")
    assert shape(src, out) == (1, 2)  # the old last line gains a terminator


def test_add_row_writes_the_row_asked_for():
    out, rid = edit.add_row(BASE, {"item": "a | b", "qty": "5"}, after="r_01")
    assert rid == "r_" + rid[2:] and re.fullmatch(r"r_[0-9a-f]{6}", rid)
    rows, _ = values(out)
    assert rows[rid]["item"] == "a | b" and rows[rid]["qty"] == "5"
    assert rows[rid]["total"] == "#REF!(unit)"
    lines = split_lines(out)
    assert lines[lines.index("| r_01 | widget | EU | 10 | 12.00 |  |") + 1].startswith(f"| {rid} ")


def test_add_row_takes_the_id_from_values_or_id():
    a, ra = edit.add_row(BASE, {"id": "r_10", "item": "x"})
    b, rb = edit.add_row(BASE, {"item": "x"}, row_key="r_10")
    assert ra == rb == "r_10" and a == b


def test_add_row_without_a_key_has_no_id():
    src = "| a | b |\n| - | - |\n| 1 | 2 |\n"
    out, rid = edit.add_row(src, {"a": "3"})
    assert rid is None and out == src + "| 3 |  |\n"


def test_a_padded_table_gets_a_padded_row_and_is_never_reflowed():
    out, _ = edit.add_row(PADDED, {"item": "cog", "qty": "1", "unit": "2"}, row_key="r_04")
    assert "| r_04 | cog    |   1 |     2 |                    |\n" in out
    wide, _ = edit.add_row(PADDED, {"item": "a much longer item"}, row_key="r_05")
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
    out, _ = edit.add_row(BASE, {"item": "café"}, row_key="r_09")
    assert "| r_09 | café |" in out


@pytest.mark.parametrize(
    "call, refusal",
    [
        (lambda: edit.add_row(BASE, {"item": "x"}, row_key="r_01"), "duplicate-row-id"),
        (lambda: edit.add_row(BASE, {"item": "x"}, row_key="r 9"), "bad-identifier"),
        (lambda: edit.add_row(BASE, {"total": "5"}), "value-in-computed-cell"),
        (lambda: edit.add_row(BASE, {"item": "---", "id": "---"}), "bad-identifier"),
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
        (lambda: edit.add_row(BASE, {"item": "a\nb"}), "line-break"),
        (lambda: edit.add_row(BASE, {"item": "a\rb"}), "line-break"),
        (lambda: edit.add_row(BASE, {"item": " a"}), "not-representable"),
        (lambda: edit.add_row(BASE, {"nope": "a"}), "no-such-column"),
        (lambda: edit.add_row(BASE, {}, after="r_99"), "no-such-row"),
        (lambda: edit.add_row(BASE, {}, after="r_01", before="r_02"), "bad-position"),
        (lambda: edit.add_row("| a |\n| - |\n", {}, row_key="r_1"), "no-key"),
        (lambda: edit.delete_row(BASE, "r_99"), "no-such-row"),
        (lambda: edit.add_row(BASE, {"id": "r_10"}, row_key="r_11"), "conflicting-id"),
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


@pytest.mark.parametrize(
    "call",
    [
        lambda: edit.add_row(text=BASE),
        lambda: edit.delete_row(BASE, row_key="r_01"),
        lambda: edit.add_column(BASE, name="n"),
        lambda: edit.delete_column(BASE, name="region"),
        lambda: edit.rename_column(BASE, "item", new="thing"),
        lambda: edit.set_formula(BASE, "total", formula="qty"),
        lambda: edit.set_declaration(BASE, "g", rhs="sum(qty)"),
        lambda: edit.delete_declaration(BASE, name="grand"),
    ],
    ids=[
        "add_row",
        "delete_row",
        "add_column",
        "delete_column",
        "rename_column",
        "set_formula",
        "set_declaration",
        "delete_declaration",
    ],
)
def test_the_text_and_the_subject_are_positional_only(call):
    """Their names differ from function to function for the same thing, so
    none of them is part of the contract."""
    with pytest.raises(TypeError, match="positional-only"):
        call()


def test_add_column_takes_no_per_row_values():
    """`values` names a row's cells by column in add_row; add_column gives
    every cell `value` and has no second meaning for the word."""
    with pytest.raises(TypeError, match="values"):
        edit.add_column(BASE, "n", values={"r_01": "x"})


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


def keys_of(text):
    return [r["id"] for r in parse(text)[2]]


def test_a_row_goes_where_its_key_sorts_when_the_rows_are_in_key_order():
    out, _ = edit.add_row(BASE, {"item": "x"}, row_key="r_025")
    assert keys_of(out) == ["r_01", "r_02", "r_025", "r_03", "r_04"]
    out, _ = edit.add_row(BASE, {"item": "x"}, row_key="r_00")
    assert keys_of(out) == ["r_00", "r_01", "r_02", "r_03", "r_04"]


def test_a_row_goes_last_when_the_rows_are_not_in_key_order():
    r01 = "| r_01 | widget | EU | 10 | 12.00 |  |\n"
    src = BASE.replace(r01, "").replace("| r_04 |", r01 + "| r_04 |")
    out, _ = edit.add_row(src, {"item": "x"}, row_key="r_025")
    assert keys_of(out) == ["r_02", "r_03", "r_01", "r_04", "r_025"]


def test_end_places_a_row_last_whatever_its_key():
    out, _ = edit.add_row(BASE, {"item": "x"}, row_key="r_00", end=True)
    assert keys_of(out)[-1] == "r_00"
    with pytest.raises(edit.EditRefused) as e:
        edit.add_row(BASE, {"item": "x"}, after="r_01", end=True)
    assert e.value.reason == "bad-position"


UNTERMINATED = "key := id\n\n" + BASE.split("\n\n")[0].replace("# parts on hand\n", "")


@pytest.mark.parametrize(
    "op",
    [
        lambda t: edit.delete_row(t, "r_04"),
        lambda t: edit.delete_declaration(t + "\ng := sum(qty)", "g"),
    ],
    ids=["delete_row", "delete_declaration"],
)
def test_removing_an_unterminated_last_line_keeps_the_file_unterminated(op):
    assert not UNTERMINATED.endswith("\n")
    out = op(UNTERMINATED)
    assert not out.endswith("\n")
    evaluate(out)


def test_removing_an_unterminated_last_line_after_a_blank_line_keeps_the_blank_line():
    """A blank line without its terminator is no line, so the file then ends in
    the blank line's terminator: the caveat docs/editing-api.md states."""
    src = BASE + "\ng := sum(qty)"
    out = edit.delete_declaration(src, "g")
    assert out == BASE + "\n"


@pytest.mark.parametrize(
    "op",
    [
        lambda t: edit.set_declaration(t, "g", "sum(a)"),
        lambda t: edit.set_declaration(t, "n", "count(id)"),
        lambda t: edit.delete_declaration(t, "n"),
        lambda t: edit.rename_column(t, "a", "b"),
        lambda t: edit.add_row(t, {"a": "2"}, row_key="r2")[0],
        lambda t: edit.add_row(t, {"a": "2"}, after="r1")[0],
        lambda t: edit.delete_row(t, "r1"),
    ],
)
def test_declarations_above_the_table(op):
    src = "key := id\nn := count(a)\n| id | a |\n| --- | --- |\n| r1 | 1 |\n"
    out = op(src)
    assert out.count("\n") - src.count("\n") in (-1, 0, 1)
    evaluate(out)


def test_a_new_declaration_above_the_table_goes_after_the_last_one():
    src = "key := id\n| id | a |\n| --- | --- |\n| r1 | 1 |\n"
    assert edit.set_declaration(src, "g", "sum(a)") == (
        "key := id\ng := sum(a)\n| id | a |\n| --- | --- |\n| r1 | 1 |\n"
    )


def test_untouched_cells_keep_their_bytes_when_not_nfc():
    nfd = unicodedata.normalize("NFD", "caf\u00e9")
    src = f"| id | a | {nfd} |\n| --- | --- | --- |\n| r1 | 1 | {nfd} |\n\nkey := id\n"
    out, _ = edit.add_row(src, {"a": "2"}, row_key="r2")
    assert out.startswith(src.split("\n\n")[0])
    out = edit.add_column(src, "z")
    assert out.splitlines()[2] == f"| r1 | 1 | {nfd} |  |"


def test_a_rename_in_a_line_that_is_not_nfc_finds_every_reference():
    nfd = unicodedata.normalize("NFD", "caf\u00e9")
    src = (
        f"| id | {nfd} | t = {nfd} * 2 |\n| --- | --- | --- |\n| r1 | 1 |  |\n\n"
        f"key := id\ng := sum({nfd})\n"
    )
    out = edit.rename_column(src, "caf\u00e9", "n")
    assert (
        out
        == "| id | n | t = n * 2 |\n| --- | --- | --- |\n| r1 | 1 |  |\n\nkey := id\ng := sum(n)\n"
    )


def test_a_string_literal_in_a_header_if_is_not_renamed():
    src = (
        '| id | qty | t = if(qty = "qty", 1, 0) |\n'
        "| --- | --- | --- |\n| r1 | qty |  |\n\nkey := id\n"
    )
    out = edit.rename_column(src, "qty", "n")
    assert out.splitlines()[0] == '| id | n | t = if(n = "qty", 1, 0) |'


def test_a_row_that_would_not_read_back_is_refused(monkeypatch):
    """The read-back is the last check, for a gap in the writer: here one that
    forgets to escape a pipe while keeping the field count."""
    monkeypatch.setattr(edit, "escape_cell", lambda c: c.replace("|", "/"))
    with pytest.raises(edit.EditRefused) as e:
        edit.add_row(BASE, {"item": "a|b"}, row_key="r_09")
    assert e.value.reason == "not-representable"


def test_a_rename_that_changes_which_name_an_aggregate_reports_is_allowed():
    """§8 reports the first name by code point among an aggregate's errors, so
    renaming `id` to `é` moves `#REF!(id)` behind `#REF!(qty)`. Both are the
    same error to the rename's check: it changes no number."""
    src = (
        "| id | qty | n = if(qty > 0, id, 0) |\n| --- | --- | --- |\n"
        "| r_1 | 10 |  |\n| r_2 | x |  |\n\nkey := id\ng := max(n)\n"
    )
    out = edit.rename_column(src, "id", "é")
    assert evaluate(out)[1] == {"g": "#REF!(qty)"} and evaluate(src)[1] == {"g": "#REF!(id)"}


def test_a_declaration_whose_name_is_not_nfc_is_replaced_in_place():
    nfd = unicodedata.normalize("NFD", "caf\u00e9")
    src = f"| id | a |\n| --- | --- |\n| r1 | 1 |\n\nkey := id\n{nfd} := sum(a)\n"
    out = edit.set_declaration(src, "caf\u00e9", "max(a)")
    assert out == src.replace("sum(a)", "max(a)")


@pytest.mark.parametrize("name", ["empty", "cycle", "overflow"])
@pytest.mark.parametrize("onto", [False, True], ids=["from", "onto"])
def test_a_column_named_like_an_error_shape_can_be_renamed(name, onto):
    """`cycle`, `empty` and `overflow` are column names as well as `#REF!`
    shapes (§8), so `#REF!(empty)` may be a broken reference to a column."""
    old, new = ("a", name) if onto else (name, "e2")
    src = (
        f"| id | {old} | t = {old} + 1 | u = nope |\n| --- | --- | --- | --- |\n"
        f"| r_1 | x |  |  |\n| r_2 | 2 |  |  |\n\nkey := id\ng := sum({old})\n"
    )
    out = edit.rename_column(src, old, new)
    assert evaluate(out)[1] == {"g": f"#REF!({new})"}


def test_a_rename_that_turns_a_number_into_an_error_is_refused(monkeypatch):
    """The value check still catches a rename that would change a number into
    an error: here the renamer is made to miss the reference in a formula."""
    monkeypatch.setattr(edit, "_formula_refs", lambda f: [])
    src = "| id | a | t = a + 1 |\n| --- | --- | --- |\n| r_1 | 2 |  |\n\nkey := id\n"
    with pytest.raises(edit.EditRefused) as e:
        edit.rename_column(src, "a", "b")
    assert e.value.reason == "rename-changes-values"


def test_after_an_unterminated_last_row_a_mixed_file_takes_crlf():
    """The row that loses its place as last line takes CRLF if the file has
    any, as `rowspec add-row` has done since #200."""
    src = "key := id\n\n| id | a |\r\n| --- | --- |\r\n| r_1 | x |"
    out, _ = edit.add_row(src, {"a": "z"}, row_key="r_2")
    assert out == src + "\r\n| r_2 | z |"
