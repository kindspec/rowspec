# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The editing subcommands, and `--help` naming the command it describes (#197).

Each subcommand is a thin layer over `rowspec.edit`, whose diff shape and
refusals `test_edit.py` covers. What is tested here is the layer: the file is
edited in place, its bytes are untouched when the edit is refused, and the
refusal's identifier is printed where a program can read it.
"""

import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import cli, parse  # noqa: E402

SRC = (
    "| id | item | qty | unit | total = qty * unit |\r\n"
    "| --- | --- | --: | --: | --: |\r\n"
    "| r_01 | widget | 10 | 12.00 |  |\r\n"
    "| r_02 | gadget | 3 | 4.50 |  |\r\n"
    "\r\n"
    "key := id\r\n"
    "grand := sum(total)\r\n"
)


@pytest.fixture
def table(tmp_path):
    p = tmp_path / "t.mdtbl"
    p.write_bytes(SRC.encode())
    return p


@pytest.mark.parametrize("cmd", list(cli.COMMANDS))
def test_help_names_the_command_it_describes(cmd, capsys):
    with pytest.raises(SystemExit) as e:
        cli.main([cmd, "--help"])
    assert e.value.code == 0
    assert capsys.readouterr().out.startswith(f"usage: rowspec {cmd} ")


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_top_level_help_lists_every_command(flag, capsys):
    assert cli.main([flag]) == 0
    out = capsys.readouterr().out
    assert out.startswith("usage: rowspec [COMMAND]")
    for cmd in cli.COMMANDS:
        assert f"\n  {cmd} " in out


def test_add_row_with_a_chosen_id_and_position(table, capsys):
    assert (
        cli.main(["add-row", str(table), "bolt", "4", "0.10", "--id", "r_09", "--after", "r_01"])
        == 0
    )
    assert "added id=r_09" in capsys.readouterr().out
    lines = table.read_bytes().decode().split("\r\n")
    assert lines[3] == "| r_09 | bolt | 4 | 0.10 |  |"


def test_add_row_before_a_key(table):
    assert cli.main(["add-row", str(table), "bolt", "4", "0.10", "--before", "r_01"]) == 0
    assert parse(table.read_text(encoding="utf-8"))[2][0]["item"] == "bolt"


@pytest.mark.parametrize(
    "args, code",
    [
        (["add-row", "{}", "x", "1", "1", "--id", "r_01"], "[duplicate-row-id]"),
        (["add-row", "{}", "x", "1", "1", "--after", "r_99"], "[no-such-row]"),
        (["add-row", "{}", "x", "1"], "expected 3 value(s)"),
        (["add-column", "{}", "qty"], "[duplicate-column]"),
        (["add-column", "{}", "t2", "--formula", "qty ^ 2"], "[malformed-formula]"),
        (["delete-column", "{}", "unit"], "[column-referenced]"),
        (["rename-column", "{}", "qty", "unit"], "[duplicate-column]"),
        (["rename-column", "{}", "qty", "a b"], "[bad-identifier]"),
    ],
)
def test_a_refused_edit_leaves_the_file_untouched(table, capsys, args, code):
    assert cli.main([a.format(table) for a in args]) == 1
    assert code in capsys.readouterr().err
    assert table.read_bytes() == SRC.encode()


def test_add_column(table):
    assert cli.main(["add-column", str(table), "note", "--after", "item", "--value", "x"]) == 0
    assert table.read_bytes().decode().split("\r\n")[:3] == [
        "| id | item | note | qty | unit | total = qty * unit |",
        "| --- | --- | --- | --: | --: | --: |",
        "| r_01 | widget | x | 10 | 12.00 |  |",
    ]


def test_add_computed_column(table):
    assert cli.main(["add-column", str(table), "t2", "--formula", "total * 2"]) == 0
    assert parse(table.read_text(encoding="utf-8"))[1]["t2"] == "total * 2"


def test_delete_column(table):
    assert cli.main(["delete-column", str(table), "item"]) == 0
    assert (
        table.read_bytes().decode().split("\r\n")[0] == "| id | qty | unit | total = qty * unit |"
    )


def test_rename_column(table, capsys):
    assert cli.main(["rename-column", str(table), "qty", "quantity"]) == 0
    assert "renamed column qty to quantity" in capsys.readouterr().out
    assert table.read_bytes() == SRC.replace("qty", "quantity").encode()


def test_check_is_still_the_default_command(table):
    assert cli.main([str(table)]) == 0


def test_add_row_goes_where_its_key_sorts_by_default(table):
    assert cli.main(["add-row", str(table), "bolt", "4", "0.10", "--id", "r_015"]) == 0
    assert [r["id"] for r in parse(table.read_text(encoding="utf-8"))[2]] == [
        "r_01",
        "r_015",
        "r_02",
    ]


def test_add_row_end_places_it_last(table):
    assert cli.main(["add-row", str(table), "bolt", "4", "0.10", "--id", "r_00", "--end"]) == 0
    assert [r["id"] for r in parse(table.read_text(encoding="utf-8"))[2]][-1] == "r_00"
