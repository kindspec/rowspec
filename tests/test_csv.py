"""CSV mode: the refusals, on files nobody migrated.

Fixtures are byte literals rather than checked-in files on purpose. A CRLF
line ending, a UTF-8 BOM and an NFD identifier are exactly the three things a
git checkout, an editor and a whitespace hook each silently normalise away, so
a fixture that has to survive all three on disk is a fixture that stops testing
what it claims to.
"""

import json
import os
import re
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import cli  # noqa: E402
from rowspec.csvmode import check_file  # noqa: E402
from rowspec.table import Malformed  # noqa: E402

# A realistic mess: a BOM, CRLF everywhere, a quoted field holding both a comma
# and a newline, doubled quotes, a ragged row, a plainly duplicated key, and two
# ids that render identically because one is NFC and the other NFD.
MESSY = (
    b"\xef\xbb\xbfid,name,note,region\r\n"
    b'r_01,Ada,"Lovelace, Countess\r\nof Lovelace",UK\r\n'
    b'r_02,Grace,"said ""hi""",US\r\n'
    b"caf\xc3\xa9,Chen,precomposed e-acute,CN\r\n"
    b"cafe\xcc\x81,Chen again,decomposed e-acute,CN\r\n"
    b"r_04,Short,missing a field\r\n"
    b"r_02,Repeat,plainly duplicated key,FR\r\n"
)

CONFLICTED = (
    b"id,name\n"
    b"r_01,Ada\n"
    b"<<<<<<< HEAD\n"
    b"r_02,Grace\n"
    b"=======\n"
    b"r_02,Grace Hopper\n"
    b">>>>>>> feature/rename\n"
)

CLEAN = b"id,name,pop,joined\nr_01,Ada,10,2020-01-02\nr_02,Grace,20,2020-03-04\n"


def write(tmp_path, name, data, sidecar=None):
    p = tmp_path / name
    p.write_bytes(data)
    if sidecar is not None:
        (tmp_path / (name + ".rowspec.json")).write_text(json.dumps(sidecar))
    return str(p)


def rules(findings):
    return sorted({f.rule for f in findings})


def messages(findings):
    return "\n".join(str(f) for f in findings)


# --------------------------------------------------------------------------
# Checkable on a bare CSV, with no sidecar at all.
# --------------------------------------------------------------------------


def test_conflict_marker_is_refused_where_csv_parses_it_as_data(tmp_path):
    """SPEC.md §9.1. Python's csv module reads this file as seven happy rows."""
    import csv
    import io

    assert len(list(csv.reader(io.StringIO(CONFLICTED.decode())))) == 7

    f = write(tmp_path, "c.csv", CONFLICTED)
    found = check_file(f)
    assert rules(found) == ["conflict-marker"]
    assert "<<<<<<< HEAD" in messages(found)
    assert ">>>>>>> feature/rename" in messages(found)


def test_lone_equals_line_is_not_a_conflict_marker(tmp_path):
    """Git never emits `=======` without opening with `<<<<<<<`, and a CSV cell
    legitimately can. Flagging it would be a false positive."""
    f = write(tmp_path, "e.csv", b"id,rule\nr_01,=======\n")
    assert check_file(f) == []


def test_duplicate_column_name(tmp_path):
    f = write(tmp_path, "d.csv", b"id,name,name\nr_01,a,b\n")
    found = check_file(f)
    assert rules(found) == ["duplicate-column"]
    assert "duplicate column name 'name'" in messages(found)


def test_column_names_collide_after_nfc_and_the_error_shows_codepoints(tmp_path):
    f = write(tmp_path, "n.csv", "id,caf\u00e9,cafe\u0301\nr_01,a,b\n".encode())
    found = check_file(f)
    assert rules(found) == ["duplicate-column"]
    assert "U+0065 U+0301" in found[0].detail


def test_format_character_in_a_column_name(tmp_path):
    """SPEC.md §3 rejects Cf characters in identifiers. A zero-width space makes
    a column that renders as `id` but can never be selected by that name."""
    f = write(tmp_path, "z.csv", "i\u200bd,name\nr_01,a\n".encode())
    found = check_file(f)
    assert "invisible-in-name" in rules(found)
    assert "U+200B" in messages(found)


def test_field_count(tmp_path):
    f = write(tmp_path, "r.csv", b"id,name,region\nr_01,Ada,UK\nr_02,Grace\n")
    found = check_file(f)
    assert rules(found) == ["field-count"]
    assert "row id='r_02' has 2 field(s), the header declares 3" in messages(found)


def test_no_table(tmp_path):
    with pytest.raises(Malformed, match="no table"):
        check_file(write(tmp_path, "empty.csv", b""))
    with pytest.raises(Malformed, match="no table"):
        check_file(write(tmp_path, "blank.csv", b"\n\n\n"))


def test_invalid_utf8_is_refused(tmp_path):
    with pytest.raises(Malformed, match="not valid UTF-8"):
        check_file(write(tmp_path, "l1.csv", b"id,name\nr_01,Gr\xe9goire\n"))


# --------------------------------------------------------------------------
# The two softenings: warn, never refuse.
# --------------------------------------------------------------------------


def test_crlf_and_bom_warn_but_do_not_refuse(tmp_path):
    f = write(tmp_path, "w.csv", b"\xef\xbb\xbfid,name\r\nr_01,Ada\r\n")
    found = check_file(f)
    assert rules(found) == ["bom", "crlf"]
    assert all(x.level == "warn" for x in found)


def test_bom_does_not_break_the_declared_key(tmp_path):
    """The BOM lands inside the first column's name. If it were not stripped,
    `key: "id"` would fail to resolve and the check would silently weaken."""
    f = write(tmp_path, "b.csv", b"\xef\xbb\xbfid,name\nr_01,Ada\nr_01,Grace\n", {"key": "id"})
    assert "duplicate-key" in rules(check_file(f))


def test_quoted_commas_and_embedded_newlines_are_not_false_positives(tmp_path):
    f = write(tmp_path, "q.csv", b'id,note\nr_01,"a, b\nc, d"\nr_02,plain\n')
    assert check_file(f) == []


def test_a_clean_csv_produces_nothing(tmp_path):
    assert check_file(write(tmp_path, "ok.csv", CLEAN)) == []


# --------------------------------------------------------------------------
# Unlocked by the sidecar.
# --------------------------------------------------------------------------


def test_duplicate_key(tmp_path):
    f = write(tmp_path, "k.csv", MESSY, {"key": "id"})
    found = check_file(f)
    assert "duplicate-key" in rules(found)
    assert "duplicate key id='r_02' — 2 rows share it" in messages(found)


def test_keys_that_render_identically_are_one_key(tmp_path):
    """SPEC.md §3: identifiers compare after NFC. `café` typed two ways is one
    id, so these rows collide -- and the error has to print the codepoints,
    because the two ids are visually indistinguishable."""
    f = write(tmp_path, "k.csv", MESSY, {"key": "id"})
    dup = [x for x in check_file(f) if x.rule == "duplicate-key" and "caf" in str(x)]
    assert len(dup) == 1
    assert "U+00E9" in dup[0].detail and "U+0065 U+0301" in dup[0].detail


def test_messy_file_reports_every_kind_at_once(tmp_path):
    f = write(tmp_path, "m.csv", MESSY, {"key": "id"})
    assert rules(check_file(f)) == ["bom", "crlf", "duplicate-key", "field-count"]


def test_ragged_row_is_named_by_its_key(tmp_path):
    f = write(tmp_path, "m.csv", MESSY, {"key": "id"})
    assert "row id='r_04' has 3 field(s)" in messages(check_file(f))


def test_order_column_mixing_types_is_refused(tmp_path):
    f = write(
        tmp_path,
        "o.csv",
        b"id,when\nr_01,2020-01-02\nr_02,Q1 2020\n",
        {"key": "id", "order": "when"},
    )
    found = check_file(f)
    assert rules(found) == ["order-mixed-types"]
    assert "date" in messages(found) and "text" in messages(found)


def test_declared_order_type_is_checked_against_the_data(tmp_path):
    f = write(
        tmp_path,
        "o.csv",
        b"id,when\nr_01,Q1\nr_02,Q2\n",
        {"key": "id", "order": "when", "order_type": "date"},
    )
    assert rules(check_file(f)) == ["order-type-mismatch"]


def test_order_column_must_exist(tmp_path):
    f = write(tmp_path, "o.csv", CLEAN, {"key": "id", "order": "joned"})
    with pytest.raises(Malformed, match="did you mean 'joined'"):
        check_file(f)


def test_non_finite_order_value(tmp_path):
    f = write(tmp_path, "o.csv", b"id,n\nr_01,1\nr_02,1e999\n", {"key": "id", "order": "n"})
    assert "order-non-finite" in rules(check_file(f))


def test_declared_column_types(tmp_path):
    f = write(
        tmp_path,
        "t.csv",
        b"id,pop\nr_01,10\nr_02,n/a\nr_03,\n",
        {"key": "id", "columns": {"pop": "number"}},
    )
    found = check_file(f)
    assert rules(found) == ["column-type"]
    assert "row id='r_02' has pop='n/a', which is not a number" in messages(found)
    assert "r_03" not in messages(found), "a blank is not a type error"


def test_thousands_separator_is_not_a_number(tmp_path):
    """SPEC.md §8 refuses thousands separators rather than interpreting them."""
    f = write(
        tmp_path, "t.csv", b'id,pop\nr_01,"1,234"\n', {"key": "id", "columns": {"pop": "number"}}
    )
    assert rules(check_file(f)) == ["column-type"]


def test_python_float_quirks_are_not_numbers(tmp_path):
    """`float('1_0')`, `float('nan')` and `float(' 1 ')` all succeed in Python.
    Agreeing with this implementation must not require reproducing that."""
    f = write(
        tmp_path,
        "t.csv",
        b"id,pop\nr_01,1_0\nr_02,nan\n",
        {"key": "id", "columns": {"pop": "number"}},
    )
    assert len([x for x in check_file(f) if x.rule == "column-type"]) == 2


# --------------------------------------------------------------------------
# The sidecar itself.
# --------------------------------------------------------------------------


def test_sidecar_is_optional(tmp_path):
    assert check_file(write(tmp_path, "ok.csv", CLEAN)) == []


def test_malformed_sidecar_is_refused_not_ignored(tmp_path):
    p = write(tmp_path, "x.csv", CLEAN)
    (tmp_path / "x.csv.rowspec.json").write_text('{"key": "id",}')
    with pytest.raises(Malformed, match="not valid JSON"):
        check_file(p)


def test_unknown_declaration_is_refused_with_a_suggestion(tmp_path):
    p = write(tmp_path, "x.csv", CLEAN, {"kye": "id"})
    with pytest.raises(Malformed, match="did you mean 'key'"):
        check_file(p)


def test_duplicate_declaration_is_refused_rather_than_last_one_wins(tmp_path):
    """SPEC.md §9.4. JSON's own rule is last-one-wins, which is precisely the
    silent overwrite this refusal exists to prevent."""
    p = write(tmp_path, "x.csv", CLEAN)
    (tmp_path / "x.csv.rowspec.json").write_text('{"key": "id", "key": "name"}')
    with pytest.raises(Malformed, match="duplicate declaration 'key'"):
        check_file(p)


def test_order_without_key_is_refused(tmp_path):
    """SPEC.md §6: without a key, tied order values fall back to file position."""
    p = write(tmp_path, "x.csv", CLEAN, {"order": "joined"})
    with pytest.raises(Malformed, match="'order' requires 'key'"):
        check_file(p)


def test_bad_column_type_name(tmp_path):
    p = write(tmp_path, "x.csv", CLEAN, {"columns": {"pop": "integer"}})
    with pytest.raises(Malformed, match="not one of number, date, text"):
        check_file(p)


def test_directory_sidecar_applies_by_glob(tmp_path):
    """Fifty CSVs keyed the same way should not need fifty sidecars."""
    (tmp_path / ".rowspec.json").write_text(json.dumps({"*.csv": {"key": "id"}}))
    p = write(tmp_path, "a.csv", b"id,name\nr_01,a\nr_01,b\n")
    assert "duplicate-key" in rules(check_file(p))


def test_per_file_sidecar_wins_over_the_directory_one(tmp_path):
    (tmp_path / ".rowspec.json").write_text(json.dumps({"*.csv": {"key": "name"}}))
    p = write(tmp_path, "a.csv", b"id,name\nr_01,x\nr_02,x\n", {"key": "id"})
    assert check_file(p) == []


def test_tsv_delimiter_is_taken_from_the_extension(tmp_path):
    p = write(tmp_path, "a.tsv", b"id\tname\nr_01\ta\nr_01\tb\n")
    (tmp_path / "a.tsv.rowspec.json").write_text(json.dumps({"key": "id"}))
    assert "duplicate-key" in rules(check_file(p))


def test_declared_delimiter(tmp_path):
    p = write(tmp_path, "a.csv", b"id;name\nr_01;a\nr_01;b\n", {"key": "id", "delimiter": ";"})
    assert "duplicate-key" in rules(check_file(p))


# --------------------------------------------------------------------------
# The CLI, which is the whole product surface.
# --------------------------------------------------------------------------


def test_check_verb_and_exit_codes(tmp_path, capsys):
    write(tmp_path, "ok.csv", CLEAN)
    assert cli.main(["check", str(tmp_path)]) == 0
    write(tmp_path, "bad.csv", CONFLICTED)
    assert cli.main(["check", str(tmp_path)]) == 1


def test_warnings_alone_do_not_fail_unless_strict(tmp_path, capsys):
    write(tmp_path, "w.csv", b"\xef\xbb\xbfid,name\r\nr_01,Ada\r\n")
    assert cli.main(["check", str(tmp_path)]) == 0
    assert cli.main(["check", "--strict", str(tmp_path)]) == 1


def test_mdtbl_still_goes_through_the_full_parser(tmp_path):
    p = tmp_path / "t.mdtbl"
    p.write_text("| id | n |\n| --- | --- |\n| r_01 | 1 |\n| r_01 | 2 |\n\nkey := id\n")
    assert cli.main(["check", str(p)]) == 1


def test_a_directory_mixes_both_formats(tmp_path, capsys):
    write(tmp_path, "a.csv", CLEAN)
    (tmp_path / "b.mdtbl").write_text("| id | n |\n| --- | --- |\n| r_01 | 1 |\n")
    assert cli.main(["check", str(tmp_path)]) == 0
    assert "2 file(s) checked" in capsys.readouterr().out


def test_github_annotation_format(tmp_path, capsys):
    write(tmp_path, "bad.csv", CONFLICTED)
    cli.main(["check", "--format", "github", str(tmp_path)])
    err = capsys.readouterr().err
    assert err.startswith("::error file=")
    assert "title=rowspec::unresolved conflict marker" in err


def test_errors_never_carry_a_line_number(tmp_path, capsys):
    """The project rule: errors name entities, not offsets. A line number is
    wrong the moment anyone else edits the file."""
    write(tmp_path, "m.csv", MESSY, {"key": "id"})
    cli.main(["check", str(tmp_path)])
    err = capsys.readouterr().err
    assert not re.search(r"\bline \d", err), err


# --------------------------------------------------------------------------
# The shipped CI workflow. It is the only repo-resident configuration a forge
# executes, so the command inside it has to keep working.
# --------------------------------------------------------------------------


def test_shipped_workflow_invokes_a_command_the_cli_accepts(tmp_path, capsys):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wf = open(os.path.join(root, "docs", "ci", "rowspec-check.yml"), encoding="utf-8").read()
    runs = re.findall(r"run:\s*(rowspec check .*)", wf)
    assert runs, "the workflow no longer runs `rowspec check`"
    write(tmp_path, "bad.csv", CONFLICTED)
    for line in runs:
        args = line.split()[1:-1] + [str(tmp_path)]  # drop `rowspec`, swap the path
        assert cli.main(args) == 1, line
    assert "::error file=" in capsys.readouterr().err
