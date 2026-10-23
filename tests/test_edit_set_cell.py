# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`rowspec.edit.set_cell`: one stored cell rewritten in place, every other
byte kept, and every refusal docs/editing-api.md names.

These cases were written from docs/editing-api.md and SPEC.md at rowspec
commit b34b957 by an author who saw no implementation. The four files given
were SPEC.md, docs/editing-api.md, CONTRIBUTING.md and tests/test_edit.py,
the last for harness style only.
"""

import difflib
import os
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

# A padded table with a centred column (`:-:`), a left one (`---`) and a right
# one (`--:`), and empty stored cells in each.
ALIGNED = (
    "| id   |  name   | qty | note |\n"
    "| ---- | :-----: | --- | ---: |\n"
    "| r_01 | abcdefg | 1   |      |\n"
    "| r_02 |   abc   | 222 |   xy |\n"
    "| r_03 |         |     |    z |\n"
    "\n"
    "key := id\n"
)

WORKED = "| id   | item   | qty |\n| ---- | ------ | --: |\n| r_20 | nut    |  10 |\n\nkey := id\n"

TIGHT = "| id | qty |\n| --- | --- |\n| r_02 | 3 |\n\nkey := id\n"
NOSPACE = "|id|qty|\n|---|---|\n|r_02|3|\n\nkey := id\n"


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


def replace_once(text, old, new):
    assert text.count(old) == 1, (old, text)
    return text.replace(old, new)


def values(text):
    seq, aggs = evaluate(text)
    key = parse(text)[5]
    return {r[key]: r for r in seq}, aggs


def stored_row(text, row_key):
    parsed = parse(text)
    key = parsed[5]
    (row,) = [r for r in parsed[2] if r[key] == row_key]
    return row


# --- diff shape -------------------------------------------------------------


def mixed(text):
    """Every other line of an LF text ends in CRLF, the rest in LF."""
    *lines, last = text.split("\n")
    assert last == ""
    return "".join(line + ("\r\n" if i % 2 else "\n") for i, line in enumerate(lines))


TERMINATORS = {
    "lf": lambda t: t,
    "crlf": lambda t: t.replace("\n", "\r\n"),
    "mixed": mixed,
    "unterminated": lambda t: t[:-1],
}

# (source, row_key, column, value, old line, new line)
ONE_LINE = {
    "canonical": (
        BASE,
        "r_02",
        "qty",
        "12",
        "| r_02 | gadget | US | 3 | 4.50 |  |",
        "| r_02 | gadget | US | 12 | 4.50 |  |",
    ),
    "canonical, text": (
        BASE,
        "r_03",
        "item",
        "washer",
        "| r_03 | bolt | EU | 100 | 0.10 |  |",
        "| r_03 | washer | EU | 100 | 0.10 |  |",
    ),
    "padded, fits": (
        PADDED,
        "r_01",
        "qty",
        "7",
        "| r_01 | widget |  10 | 12.00 |                    |",
        "| r_01 | widget |   7 | 12.00 |                    |",
    ),
    "padded, too wide": (
        PADDED,
        "r_02",
        "item",
        "a much longer item",
        "| r_02 | gadget |   3 |  4.50 |                    |",
        "| r_02 | a much longer item |   3 |  4.50 |                    |",
    ),
    "key column": (
        BASE,
        "r_02",
        "id",
        "r_05",
        "| r_02 | gadget | US | 3 | 4.50 |  |",
        "| r_05 | gadget | US | 3 | 4.50 |  |",
    ),
}


@pytest.mark.parametrize("term", list(TERMINATORS))
@pytest.mark.parametrize("case", list(ONE_LINE))
def test_set_cell_changes_one_line_and_keeps_every_terminator(case, term):
    """docs/editing-api.md: `set_cell` is 1 changed line (the row), which keeps
    its own terminator; every other byte stays as it was."""
    src, row_key, column, value, old, new = ONE_LINE[case]
    src = TERMINATORS[term](src)
    out = edit.set_cell(src, row_key, column, value)
    assert out == replace_once(src, old, new)
    assert shape(src, out) == (1, 1)


@pytest.mark.parametrize("term", ["lf", "crlf"])
def test_an_unterminated_last_row_stays_unterminated(term):
    src = "key := id\n\n| id | a |\n| --- | --- |\n| r_1 | x |\n| r_2 | y |"
    src = src.replace("\n", "\r\n") if term == "crlf" else src
    out = edit.set_cell(src, "r_2", "a", "z")
    assert out == src[: -len("| r_2 | y |")] + "| r_2 | z |"
    assert shape(src, out) == (1, 1)


def test_in_a_mixed_file_each_row_keeps_its_own_terminator():
    src = "| id | a |\r\n| --- | --- |\n| r_1 | x |\r\n| r_2 | y |\n\nkey := id\r\n"
    assert edit.set_cell(src, "r_1", "a", "z") == src.replace("| r_1 | x |\r\n", "| r_1 | z |\r\n")
    assert edit.set_cell(src, "r_2", "a", "z") == src.replace("| r_2 | y |\n", "| r_2 | z |\n")


def test_the_rows_other_cells_and_decoration_keep_their_bytes():
    """Only the cell's own span changes: irregular spacing in the row's other
    cells, and `WSP` outside the pipes (§4.1.3), stay as they were."""
    row = "  |  r_1|x  |   7   | y |\t"
    src = (
        f"| id | a | b | c |\n| --- | --- | --- | --- |\n{row}\n| r_2 | p | 1 | q |\n\nkey := id\n"
    )
    out = edit.set_cell(src, "r_1", "c", "zz")
    assert out == replace_once(src, row, "  |  r_1|x  |   7   | zz |\t")


# --- padding (rule 3) -------------------------------------------------------


@pytest.mark.parametrize(
    "src, row_key, column, value, old, new",
    [
        # a padded cell keeps its width and placement: right
        (
            PADDED,
            "r_02",
            "unit",
            "1",
            "| r_02 | gadget |   3 |  4.50 |",
            "| r_02 | gadget |   3 |     1 |",
        ),
        # left: only the right side was padded
        (
            PADDED,
            "r_03",
            "item",
            "nut",
            "| r_03 | bolt   | 100 |",
            "| r_03 | nut    | 100 |",
        ),
        (
            ALIGNED,
            "r_01",
            "qty",
            "55",
            "| r_01 | abcdefg | 1   |      |",
            "| r_01 | abcdefg | 55  |      |",
        ),
        # centred: both sides were padded
        (
            ALIGNED,
            "r_02",
            "name",
            "x",
            "| r_02 |   abc   | 222 |   xy |",
            "| r_02 |    x    | 222 |   xy |",
        ),
        (
            ALIGNED,
            "r_02",
            "name",
            "abcde",
            "| r_02 |   abc   | 222 |   xy |",
            "| r_02 |  abcde  | 222 |   xy |",
        ),
        # new text that exactly fits with one space on each side
        (
            ALIGNED,
            "r_02",
            "note",
            "abcd",
            "| r_02 |   abc   | 222 |   xy |",
            "| r_02 |   abc   | 222 | abcd |",
        ),
        (
            PADDED,
            "r_01",
            "item",
            "abcdef",
            "| r_01 | widget |  10 |",
            "| r_01 | abcdef |  10 |",
        ),
    ],
    ids=[
        "right",
        "left, padded on the right",
        "left, padded on the right, wider text",
        "centred, narrower",
        "centred, wider",
        "right, exact fit",
        "left, exact fit",
    ],
)
def test_a_padded_cell_keeps_its_width_and_placement(src, row_key, column, value, old, new):
    out = edit.set_cell(src, row_key, column, value)
    assert out == replace_once(src, old, new)
    assert shape(src, out) == (1, 1)


@pytest.mark.parametrize(
    "src, row_key, column, value, old, new",
    [
        # `--:`: right
        (
            PADDED,
            "r_03",
            "qty",
            "5",
            "| r_03 | bolt   | 100 |",
            "| r_03 | bolt   |   5 |",
        ),
        # `:-:`: centred
        (
            ALIGNED,
            "r_01",
            "name",
            "xyz",
            "| r_01 | abcdefg | 1   |",
            "| r_01 |   xyz   | 1   |",
        ),
        # `---`: left
        (
            ALIGNED,
            "r_02",
            "qty",
            "4",
            "| r_02 |   abc   | 222 |",
            "| r_02 |   abc   | 4   |",
        ),
        (
            PADDED,
            "r_01",
            "item",
            "cog",
            "| r_01 | widget |  10 |",
            "| r_01 | cog    |  10 |",
        ),
    ],
    ids=["right", "centred", "left", "left, plain name column"],
)
def test_in_a_padded_table_the_widest_cell_keeps_the_column_width(
    src, row_key, column, value, old, new
):
    """A cell with one space on each side, in a padded table, keeps the
    column's width and is placed as the alignment cell says."""
    out = edit.set_cell(src, row_key, column, value)
    assert out == replace_once(src, old, new)
    assert shape(src, out) == (1, 1)


@pytest.mark.parametrize(
    "src, row_key, column, value, old, new",
    [
        (
            ALIGNED,
            "r_03",
            "name",
            "abc",
            "| r_03 |         |     |    z |",
            "| r_03 |   abc   |     |    z |",
        ),
        (
            ALIGNED,
            "r_03",
            "qty",
            "7",
            "| r_03 |         |     |    z |",
            "| r_03 |         | 7   |    z |",
        ),
        (
            ALIGNED,
            "r_01",
            "note",
            "ab",
            "| r_01 | abcdefg | 1   |      |",
            "| r_01 | abcdefg | 1   |   ab |",
        ),
    ],
    ids=["centred", "left", "right"],
)
def test_a_cell_with_no_text_is_placed_by_the_alignment_cell(src, row_key, column, value, old, new):
    out = edit.set_cell(src, row_key, column, value)
    assert out == replace_once(src, old, new)


def test_a_padded_cell_set_to_empty_keeps_its_width():
    out = edit.set_cell(PADDED, "r_01", "item", "")
    assert out == replace_once(PADDED, "| r_01 | widget |  10 |", "| r_01 |        |  10 |")
    assert stored_row(out, "r_01")["item"] == ""


@pytest.mark.parametrize(
    "src, row_key, column, value, old, new",
    [
        (
            PADDED,
            "r_01",
            "qty",
            "12345",
            "| r_01 | widget |  10 | 12.00 |",
            "| r_01 | widget | 12345 | 12.00 |",
        ),
        (
            PADDED,
            "r_01",
            "item",
            "abcdefg",
            "| r_01 | widget |  10 |",
            "| r_01 | abcdefg |  10 |",
        ),
        (
            ALIGNED,
            "r_02",
            "note",
            "abcde",
            "| r_02 |   abc   | 222 |   xy |",
            "| r_02 |   abc   | 222 | abcde |",
        ),
        (
            ALIGNED,
            "r_01",
            "name",
            "abcdefgh",
            "| r_01 | abcdefg | 1   |",
            "| r_01 | abcdefgh | 1   |",
        ),
    ],
    ids=["right", "left, one too wide", "right, one too wide", "centred widest"],
)
def test_text_too_wide_is_written_with_one_space_each_side_and_nothing_reflows(
    src, row_key, column, value, old, new
):
    """Rule 4: the value is written wider and only its line changes."""
    out = edit.set_cell(src, row_key, column, value)
    assert out == replace_once(src, old, new)
    assert shape(src, out) == (1, 1)


def test_the_worked_example_changes_only_the_digits():
    out = edit.set_cell(WORKED, "r_20", "qty", "11")
    assert out == replace_once(WORKED, "| r_20 | nut    |  10 |", "| r_20 | nut    |  11 |")


@pytest.mark.parametrize(
    "src, value, old, new",
    [
        (TIGHT, "30", "| r_02 | 3 |", "| r_02 | 30 |"),
        (NOSPACE, "30", "|r_02|3|", "|r_02|30|"),
        (NOSPACE.replace("|3|", "|3 |"), "30", "|r_02|3 |", "|r_02|30 |"),
        (TIGHT, "", "| r_02 | 3 |", "| r_02 |  |"),
        (NOSPACE, "", "|r_02|3|", "|r_02||"),
    ],
    ids=["one space", "no space", "space on the right only", "to empty", "no space, to empty"],
)
def test_an_unpadded_cell_in_an_unpadded_table_keeps_its_own_spacing(src, value, old, new):
    out = edit.set_cell(src, "r_02", "qty", value)
    assert out == replace_once(src, old, new)


@pytest.mark.parametrize(
    "cell",
    ["||", "| |"],
    ids=["empty, no space", "empty, one space"],
)
def test_an_unpadded_cell_with_no_text_is_written_with_one_space_each_side(cell):
    src = f"| id | qty | n |\n| --- | --- | --- |\n| r_02 {cell} 1 |\n\nkey := id\n"
    old = f"| r_02 {cell} 1 |"
    out = edit.set_cell(src, "r_02", "qty", "30")
    assert out == replace_once(src, old, "| r_02 | 30 | 1 |")


def test_a_padded_cell_in_an_unpadded_table_keeps_its_width():
    """The base rule: a cell with more than one space beside its text keeps
    its width when the new text fits, whatever the rest of the table does."""
    src = TIGHT.replace("| r_02 | 3 |", "| r_02 |   3 |")
    out = edit.set_cell(src, "r_02", "qty", "30")
    assert out == replace_once(src, "| r_02 |   3 |", "| r_02 |  30 |")


def test_the_widest_cell_of_a_table_that_is_not_padded_is_re_rendered():
    """One row of another width makes the table not padded: then a cell with
    one space on each side grows or shrinks with its text, while a padded
    cell still keeps its width."""
    src = PADDED.replace(
        "| r_03 | bolt   | 100 |  0.10 |                    |\n",
        "| r_03 | bolt   | 100 |  0.10 |                    |\n| r_04 | x | 1 | 2 |  |\n",
    )
    out = edit.set_cell(src, "r_03", "qty", "5")
    assert out == replace_once(src, "| r_03 | bolt   | 100 |", "| r_03 | bolt   | 5 |")
    out = edit.set_cell(src, "r_01", "qty", "7")
    assert out == replace_once(src, "| r_01 | widget |  10 |", "| r_01 | widget |   7 |")


# --- escapes, backslash, NFC ------------------------------------------------


@pytest.mark.parametrize(
    "src, value, old, new",
    [
        (NOSPACE, "a\\", "|r_02|3|", "|r_02|a\\ |"),
        (NOSPACE.replace("|3|", "|3 |"), "a\\", "|r_02|3 |", "|r_02|a\\ |"),
        (TIGHT, "a\\", "| r_02 | 3 |", "| r_02 | a\\ |"),
    ],
    ids=["no space: gains one", "space already there", "one space each side"],
)
def test_a_trailing_backslash_never_escapes_the_next_pipe(src, value, old, new):
    out = edit.set_cell(src, "r_02", "qty", value)
    assert out == replace_once(src, old, new)
    assert stored_row(out, "r_02")["qty"] == "a\\"


@pytest.mark.parametrize(
    "src, row_key, old, new",
    [
        (BASE, "r_01", "| r_01 | widget | EU |", "| r_01 | a\\|b | EU |"),
        (PADDED, "r_01", "| r_01 | widget |  10 |", "| r_01 | a\\|b   |  10 |"),
        (NOSPACE.replace("qty", "item"), "r_02", "|r_02|3|", "|r_02|a\\|b|"),
    ],
    ids=["canonical", "padded", "no space"],
)
def test_a_pipe_in_a_value_is_written_escaped_and_reads_back(src, row_key, old, new):
    out = edit.set_cell(src, row_key, "item", "a|b")
    assert out == replace_once(src, old, new)
    assert stored_row(out, row_key)["item"] == "a|b"


def test_a_value_is_written_nfc():
    nfd = unicodedata.normalize("NFD", "café")
    assert nfd != "café"
    out = edit.set_cell(BASE, "r_02", "item", nfd)
    assert out == replace_once(BASE, "| r_02 | gadget |", "| r_02 | café |")
    assert stored_row(out, "r_02")["item"] == "café"


def test_bytes_the_edit_does_not_change_are_kept_when_not_nfc():
    nfd = unicodedata.normalize("NFD", "café")
    src = (
        f"| id | a | b |\n| --- | --- | --- |\n"
        f"| r1 | {nfd} | 1 |\n| r2 | {nfd} | 2 |\n\nkey := id\n# {nfd}\n"
    )
    out = edit.set_cell(src, "r1", "b", "3")
    assert out == replace_once(src, f"| r1 | {nfd} | 1 |", f"| r1 | {nfd} | 3 |")


# --- read-back --------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    ["12", "bolt", "a b", "a | b", "a\\|b", "#4", "a\\", " x", "1 500", "", "---"],
    ids=[
        "number",
        "text",
        "inner space",
        "spaced pipe",
        "backslash pipe",
        "hash",
        "trailing backslash",
        "leading nbsp",
        "inner nbsp",
        "empty",
        "dashes",
    ],
)
@pytest.mark.parametrize("name", ["canonical", "padded", "no space"])
def test_the_set_cell_reads_back_as_requested_and_the_row_is_otherwise_unchanged(name, value):
    src = {"canonical": BASE, "padded": PADDED, "no space": NOSPACE.replace("qty", "item")}[name]
    row_key = "r_02"
    before = stored_row(src, row_key)
    out = edit.set_cell(src, row_key, "item", value)
    after = stored_row(out, row_key)
    assert after["item"] == value
    assert {c: v for c, v in after.items() if c != "item"} == {
        c: v for c, v in before.items() if c != "item"
    }
    assert shape(src, out) == (1, 1)


# --- no-ops -----------------------------------------------------------------


@pytest.mark.parametrize(
    "src, row_key, column, value",
    [
        (BASE, "r_01", "qty", "10"),
        (BASE, "r_01", "total", ""),
        (BASE.replace("\n", "\r\n"), "r_01", "item", "widget"),
        (BASE.rstrip("\n"), "r_04", "qty", "200"),
        (PADDED, "r_01", "qty", "10"),
        (PADDED, "r_02", "item", "gadget"),
        (PADDED, "r_01", "total", ""),
        (ALIGNED, "r_02", "name", "abc"),
        (ALIGNED, "r_01", "qty", "1"),
        (ALIGNED, "r_01", "note", ""),
        (NOSPACE, "r_02", "qty", "3"),
        (NOSPACE.replace("|3|", "|  3|"), "r_02", "qty", "3"),
        (TIGHT, "r_02", "id", "r_02"),
        ("| id | a |\n| --- | --- |\n| r_1 | café |\n\nkey := id\n", "r_1", "a", "café"),
    ],
    ids=[
        "canonical",
        "computed",
        "crlf",
        "unterminated",
        "padded right",
        "padded left",
        "padded computed",
        "centred",
        "left",
        "empty",
        "no space",
        "irregular padding",
        "key",
        "nfd value of an nfc cell",
    ],
)
def test_setting_a_cell_to_its_own_text_returns_the_file_byte_for_byte(src, row_key, column, value):
    assert edit.set_cell(src, row_key, column, value) == src


# --- key and order ----------------------------------------------------------


def test_setting_the_key_column_changes_the_rows_key():
    out = edit.set_cell(BASE, "r_02", "id", "r_05")
    assert out == replace_once(BASE, "| r_02 | gadget |", "| r_05 | gadget |")
    _, old_aggs = values(BASE)
    new_rows, new_aggs = values(out)
    assert "r_02" not in new_rows and new_rows["r_05"]["item"] == "gadget"
    assert new_aggs == old_aggs
    with pytest.raises(edit.EditRefused) as e:
        edit.set_cell(out, "r_02", "qty", "1")
    assert e.value.reason == "no-such-row"


ORDERED = (
    "| id | day | v | run = cumulative(v) |\n"
    "| --- | --- | --- | --- |\n"
    "| r_1 | 1 | 10 |  |\n"
    "| r_2 | 2 | 20 |  |\n"
    "\n"
    "key := id\n"
    "order := by(day)\n"
)


def test_setting_the_order_column_reorders_the_row_relative_values():
    """§6/§7: `cumulative` runs over the derived order. Moving `r_1` after
    `r_2` by its `day` gives `r_1` the running total `r_2` had."""
    out = edit.set_cell(ORDERED, "r_1", "day", "3")
    assert out == replace_once(ORDERED, "| r_1 | 1 | 10 |  |", "| r_1 | 3 | 10 |  |")
    before, _ = values(ORDERED)
    after, _ = values(out)
    assert after["r_1"]["run"] == before["r_2"]["run"]
    assert after["r_2"]["run"] != before["r_2"]["run"]
    assert after["r_2"]["run"] == values(ORDERED.replace("| 10 |", "| 20 |", 1))[0]["r_1"]["run"]


@pytest.mark.parametrize("value", ["", "x"], ids=["blank", "mixed types"])
def test_an_order_column_set_to_what_spec_refuses_is_refused(value):
    with pytest.raises(Malformed) as e:
        edit.set_cell(ORDERED, "r_1", "day", value)
    assert e.value.refusal == "bad-order-column"


# --- refusals ---------------------------------------------------------------


@pytest.mark.parametrize(
    "call, reason",
    [
        (lambda: edit.set_cell("| a | b |\n| - | - |\n| 1 | 2 |\n", "1", "b", "3"), "no-key"),
        (lambda: edit.set_cell(BASE, "r_99", "qty", "1"), "no-such-row"),
        (lambda: edit.set_cell(BASE, "r_01", "nope", "1"), "no-such-column"),
        (lambda: edit.set_cell(BASE, "r_01", "item", "a\nb"), "line-break"),
        (lambda: edit.set_cell(BASE, "r_01", "item", "a\rb"), "line-break"),
        (lambda: edit.set_cell(BASE, "r_01", "item", "a\r\nb"), "line-break"),
        (lambda: edit.set_cell(BASE, "r_01", "item", "a\n"), "line-break"),
        (lambda: edit.set_cell(BASE, "r_01", "item", " a"), "not-representable"),
        (lambda: edit.set_cell(BASE, "r_01", "item", "a "), "not-representable"),
        (lambda: edit.set_cell(BASE, "r_01", "item", "\ta"), "not-representable"),
        (lambda: edit.set_cell(BASE, "r_01", "item", "a\t"), "not-representable"),
        (lambda: edit.set_cell(BASE, "r_01", "item", " "), "not-representable"),
        (lambda: edit.set_cell(PADDED, "r_01", "qty", " 7"), "not-representable"),
        (lambda: edit.set_cell(BASE, "r_01", "id", "r_09 "), "not-representable"),
    ],
    ids=[
        "no-key",
        "no-such-row",
        "no-such-column",
        "LF",
        "CR",
        "CRLF",
        "trailing LF",
        "leading space",
        "trailing space",
        "leading tab",
        "trailing tab",
        "only a space",
        "leading space, padded",
        "trailing space, key column",
    ],
)
def test_a_request_that_cannot_be_written_is_refused_with_a_reason(call, reason):
    with pytest.raises(edit.EditRefused) as e:
        call()
    assert e.value.reason == reason


@pytest.mark.parametrize(
    "call, refusal",
    [
        (lambda: edit.set_cell(BASE, "r_01", "total", "5"), "value-in-computed-cell"),
        (lambda: edit.set_cell(PADDED, "r_01", "total", "x"), "value-in-computed-cell"),
        (lambda: edit.set_cell(BASE, "r_02", "id", "r_01"), "duplicate-row-id"),
        (lambda: edit.set_cell(BASE, "r_02", "id", ""), "bad-identifier"),
        (lambda: edit.set_cell(BASE, "r_02", "id", "r 2"), "bad-identifier"),
        (lambda: edit.set_cell(BASE, "r_02", "id", "r-2"), "bad-identifier"),
        (
            lambda: edit.set_cell(BASE + "key := item\n", "r_01", "qty", "1"),
            "duplicate-declaration",
        ),
        (
            lambda: edit.set_cell(BASE.replace("| 3 |", "| 3 | 9 |"), "r_01", "qty", "1"),
            "row-field-count",
        ),
    ],
    ids=[
        "computed",
        "computed, padded",
        "duplicate key",
        "blank key",
        "key with a space",
        "key with a hyphen",
        "refused input",
        "refused input, field count",
    ],
)
def test_a_refusal_spec_names_carries_its_identifier(call, refusal):
    with pytest.raises(Malformed) as e:
        call()
    assert e.value.refusal == refusal


def test_edit_refused_is_a_malformed():
    with pytest.raises(Malformed):
        edit.set_cell(BASE, "r_99", "qty", "1")


@pytest.mark.parametrize(
    "call",
    [
        lambda: edit.set_cell(BASE, "r_01", "qty", 12),
        lambda: edit.set_cell(BASE, "r_01", "qty", 0.5),
        lambda: edit.set_cell(BASE, "r_01", "qty", None),
        lambda: edit.set_cell(BASE, 1, "qty", "12"),
        lambda: edit.set_cell(BASE, "r_01", 3, "12"),
        lambda: edit.set_cell(BASE.encode(), "r_01", "qty", "12"),
    ],
    ids=["int value", "float value", "None value", "int row_key", "int column", "bytes text"],
)
def test_an_argument_that_is_not_a_str_is_a_type_error(call):
    with pytest.raises(TypeError):
        call()


@pytest.mark.parametrize(
    "call",
    [
        lambda: edit.set_cell(BASE, "r_01", "qty", value="12"),
        lambda: edit.set_cell(BASE, "r_01", column="qty", value="12"),
        lambda: edit.set_cell(BASE, row_key="r_01", column="qty", value="12"),
        lambda: edit.set_cell(text=BASE, row_key="r_01", column="qty", value="12"),
    ],
    ids=["value", "column", "row_key", "text"],
)
def test_every_argument_is_positional_only(call):
    with pytest.raises(TypeError, match="positional-only"):
        call()
