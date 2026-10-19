# SPDX-License-Identifier: Apache-2.0 OR MIT
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


def test_a_marker_run_that_does_not_start_the_line_is_data(tmp_path):
    """SPEC.md §4.1.12 is about a line's first seven characters. A cell
    holding `=======` after the first field does not start the line."""
    f = write(tmp_path, "e.csv", b"id,rule\nr_01,=======\nr_02,<<<<<<\n")
    assert check_file(f) == []


@pytest.mark.parametrize("line", [b"=======", b"<<<<<<<<", b">>>>>>>x", b"|||||||,a"])
def test_a_line_starting_with_seven_marker_characters_is_refused(tmp_path, line):
    """SPEC.md §4.1.12, wherever the line appears: no opening `<<<<<<<` is
    needed, and nothing has to follow the seven characters."""
    f = write(tmp_path, "m.csv", b"id\nr_01\n" + line + b"\nr_02\n")
    assert rules(check_file(f)) == ["conflict-marker"]


def test_duplicate_column_name(tmp_path):
    f = write(tmp_path, "d.csv", b"id,name,name\nr_01,a,b\n")
    found = check_file(f)
    assert rules(found) == ["duplicate-column"]
    assert "duplicate column name 'name'" in messages(found)


def test_repeated_empty_names_in_a_grouped_looking_header_are_duplicate_columns(tmp_path, capsys):
    """#92. SPEC.md §13 makes an empty header cell a column name, so five of
    them are §9.2's duplicate column. No label repeats, so this is not a
    grouped header, and it must be a finding rather than a traceback."""
    f = write(tmp_path, "g.csv", b",x,,,,\na,b,c,d,e,f\n")
    found = check_file(f)
    assert rules(found) == ["duplicate-column"]
    assert "duplicate column name an unnamed column" in messages(found)
    assert cli.main(["check", f]) == 1
    assert "duplicate column name an unnamed column" in capsys.readouterr().err


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


@pytest.mark.parametrize(
    "data",
    [
        b"id,name\nr_01,a\n\nr_02,b\n",
        b"id,name\nr_01,a\n\nr_02,b",
        b"id,name\r\nr_01,a\r\n\r\nr_02,b\r\n",
        b"id,name\nr_01,a\n\n\n",
        b"id,name\r\nr_01,a\r\n\r\n\r\n",
        b"id,name\nr_01,a\n \n",
    ],
)
def test_a_blank_line_between_rows_is_a_record_of_one_empty_field(tmp_path, data):
    """RFC 4180: an empty line is a record with one empty field, and against
    a two-field header that is a field-count mismatch. Two blank lines at the
    end are not "one at the end": the first sits between rows. A trailing line
    of spaces is not empty at all, so it is a record like any other."""
    found = check_file(write(tmp_path, "b.csv", data))
    assert rules([f for f in found if f.level == "refuse"]) == ["field-count"]


@pytest.mark.parametrize("data", [b"id,name\nr_01,a\n\n", b"id,name\r\nr_01,a\r\n\r\n"])
def test_one_blank_line_at_the_end_of_the_file_is_accepted(tmp_path, data):
    """SPEC.md §13: a single blank line after the last record is not between
    rows. fivethirtyeight's women-stem.csv, pepecash_prices.csv and
    xcp_prices.csv each end this way."""
    found = check_file(write(tmp_path, "b.csv", data))
    assert [f for f in found if f.level == "refuse"] == []


def test_a_blank_line_fits_a_one_column_file(tmp_path):
    assert check_file(write(tmp_path, "b.csv", b"name\na\n\nb\n")) == []


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


def test_bom_and_lone_cr_warn_but_do_not_refuse(tmp_path):
    """SPEC.md §13: refusals 26 (BOM) and 15 (lone CR) are warnings in CSV
    mode. A lone CR ends a record for a CSV reader but not a line for git, so
    two rows share one line in every diff and merge."""
    f = write(tmp_path, "w.csv", b"\xef\xbb\xbfid,name\rr_01,Ada\n")
    found = check_file(f)
    assert rules(found) == ["bom", "lone-cr"]
    assert all(x.level == "warn" for x in found)


def test_crlf_is_an_advisory_warning_not_a_refusal(tmp_path):
    """SPEC.md §3 accepts LF and CRLF alike. The CRLF warning is rowspec's
    advisory, not a spec requirement, and `--strict` refusing it is part of
    the action's documented `strict` input."""
    found = check_file(write(tmp_path, "crlf.csv", b"id,name\r\nr_01,Ada\r\n"))
    assert rules(found) == ["crlf"]
    assert all(x.level == "warn" for x in found)


def test_a_cr_that_is_part_of_crlf_is_not_a_lone_cr(tmp_path):
    f = write(tmp_path, "mixed.csv", b"id,name\r\nr_01,Ada\nr_02,Grace\r\n")
    assert rules(check_file(f)) == ["crlf"]


def test_crlf_and_a_lone_cr_are_reported_separately(tmp_path):
    f = write(tmp_path, "both.csv", b"id,name\r\nr_01,Ada\rr_02,Grace\r\n")
    assert rules(check_file(f)) == ["crlf", "lone-cr"]


def test_bom_does_not_break_the_declared_key(tmp_path):
    """The BOM lands inside the first column's name. If it were not stripped,
    `key: "id"` would fail to resolve and the check would silently weaken."""
    f = write(tmp_path, "b.csv", b"\xef\xbb\xbfid,name\nr_01,Ada\nr_01,Grace\n", {"key": "id"})
    assert "duplicate-key" in rules(check_file(f))


def test_quoted_commas_and_embedded_newlines_are_not_false_positives(tmp_path):
    f = write(tmp_path, "q.csv", b'id,note\nr_01,"a, b\nc, d"\nr_02,plain\n')
    assert check_file(f) == []


def test_a_quote_left_open_is_refused_rather_than_swallowing_rows(tmp_path):
    """RFC 4180 generates no record from an open quote to the end of the file.
    Python's reader folds `r_02` into r_01's cell instead, and says nothing."""
    f = write(tmp_path, "u.csv", b'id,note\nr_01,"abc\nr_02,b\n')
    found = check_file(f)
    assert rules(found) == ["unterminated-quote"]
    assert "abc" in messages(found)


@pytest.mark.parametrize(
    "data",
    [
        b'id,note\nr_01,"say ""hi"""\nr_02,b\n',
        b'id,note\nr_01,""\nr_02,"a,b"\n',
        b'id,note\r\nr_01,"a"\r\nr_02,"b"',
    ],
)
def test_well_formed_quoting_is_accepted(tmp_path, data):
    """RFC 4180 §2: a quoted field, with `""` for a quote inside it, closed
    by a lone `"` that the delimiter, a line break or the end of the file
    follows."""
    found = check_file(write(tmp_path, "q.csv", data))
    assert [f for f in found if f.level == "refuse"] == []


@pytest.mark.parametrize("field", [b'5" pipe', b'a"', b'"a"b', b'"a" ', b'"a""b"c'])
def test_a_stray_quote_is_refused(tmp_path, field):
    """SPEC.md §13 and RFC 4180 §2: a `"` inside an unquoted field (rule 5),
    or anything but the delimiter or a line break after a closing quote,
    is refused. A reader otherwise guesses what the field holds."""
    f = write(tmp_path, "s.csv", b"id,note\nr_01," + field + b"\nr_02,b\n")
    assert rules(check_file(f)) == ["stray-quote"]


def test_two_stray_quote_findings_with_the_same_opening_are_told_apart(tmp_path):
    """The shape of owid's scripts/input/yougov/mapping.csv: unescaped quotes
    inside two quoted fields whose first 40 characters are the same. Shown
    as 40 characters from the field's start with no row, the two findings
    read identically; each now names its row, as every other CSV-mode
    finding does."""
    data = (
        b"id,question,scale\r\n"
        b'q1,"On a scale from "Not at all" to "Fully" rate people",5\r\n'
        b'q2,"On a scale from "Not at all" to "Fully" rate the state",5\r\n'
    )
    found = [f for f in check_file(write(tmp_path, "m.csv", data)) if f.level == "refuse"]
    assert [str(f).split(":")[0] for f in found] == ["row id='q1'", "row id='q2'"]
    assert len({str(f) for f in found}) == 2


def test_a_stray_quote_in_a_short_field_is_quoted_up_to_its_end(tmp_path):
    f = write(tmp_path, "s.csv", b'id,a,b\nr_01,x"y,next\n')
    assert messages(check_file(f)) == "row id='r_01': the field 'x\"y' holds a stray quote"


def test_a_stray_quote_names_its_row_by_the_declared_key(tmp_path):
    f = write(tmp_path, "k.csv", b'note,sku\nx"y,s_1\n', {"key": "sku"})
    assert messages(check_file(f)).startswith("row sku='s_1':")


@pytest.mark.parametrize("eol", [b"\r\n", b"\r"], ids=["crlf", "lone-cr"])
def test_a_stray_quote_with_no_first_field_names_the_record(tmp_path, eol):
    """With the first field empty and no key, the row is named by its record
    number, counted over data records. CRLF ends one record, not two, and a
    lone CR ends one too (RFC 4180 record boundaries, SPEC.md §13)."""
    data = eol.join([b"id,note", b"r_01,a", b',x"y', b""])
    found = [f for f in check_file(write(tmp_path, "r.csv", data)) if f.level == "refuse"]
    assert messages(found) == "record 2: the field 'x\"y' holds a stray quote"


def test_a_doubled_quote_inside_a_shown_field_is_kept(tmp_path):
    """`""` inside a quoted field is one quote, not its end, so a delimiter
    after it is still inside the field and the field is shown whole."""
    f = write(tmp_path, "d.csv", b'id,a,b\nr_01,"x"",y"z,next\n')
    assert messages(check_file(f)) == "row id='r_01': the field '\"x\"\",y\"z' holds a stray quote"


def test_a_stray_quote_names_its_row_by_the_first_column_with_the_key_name(tmp_path):
    f = write(tmp_path, "k.csv", b'sku,sku\ns_1,x"y\n', {"key": "sku"})
    assert messages(check_file(f)).startswith("row sku='s_1':")


def test_a_stray_quote_in_the_header_names_the_header(tmp_path):
    f = write(tmp_path, "h.csv", b'id,na"me\nr_01,a\n')
    assert messages(check_file(f)).startswith("the header row:")


def test_the_cap_on_stray_quotes_counts_fields(tmp_path):
    rows = b"".join(b'r_%d,x"y,z"w\n' % i for i in range(3))
    found = check_file(write(tmp_path, "c.csv", b"id,a,b\n" + rows))
    assert str(found[-1]) == "\u2026 and 3 more field(s) with the same problem"


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


@pytest.mark.parametrize(
    "value",
    [
        b"r 1",
        b"",
        b"r\xe2\x80\x8b1",
        b"r\xc2\xa01",
        b"\xc2\xa0r1",
        b"r1\xc2\xa0",
        b"\xe3\x80\x80r1",
    ],
)
def test_a_key_value_that_could_render_like_another_is_refused(tmp_path, value):
    """SPEC.md §13: an empty key value, or one holding whitespace (an NBSP
    included) or a `Cf` character, is refused when a key is declared. Only
    ASCII space and tab are trimmed (§4.1.4), so a leading or trailing NBSP
    or ideographic space is part of the value, and refused."""
    f = write(tmp_path, "i.csv", b"id,name\n" + value + b",a\nr_2,b\n", {"key": "id"})
    assert rules(check_file(f)) == ["key-not-identifier"]


@pytest.mark.parametrize("value", [b"002RadioTV.do", b"Africa/Abidjan", b"r-1", b" r1\t"])
def test_key_punctuation_outside_the_allowlist_is_accepted(tmp_path, value):
    """The rest of §4.1.9's allowlist is for formulas, and a CSV has none.
    These are real registry ids (iptv-org/database)."""
    f = write(tmp_path, "i.csv", b"id,name\n" + value + b",a\nr_2,b\n", {"key": "id"})
    assert check_file(f) == []


def test_a_key_rule_needs_a_declared_key(tmp_path):
    f = write(tmp_path, "i.csv", b"id,name\nr 1,a\n,b\n")
    assert check_file(f) == []


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
    # §4.1.6 makes `1e999` text, so the non-finite number is a digit string
    # that matches `number` and is beyond binary64.
    big = b"9" * 400
    f = write(tmp_path, "o.csv", b"id,n\nr_01,1\nr_02," + big + b"\n", {"key": "id", "order": "n"})
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


def test_a_lone_cr_is_a_warning_on_the_cli(tmp_path, capsys):
    write(tmp_path, "lonecr.csv", b"a,b\r1,2\n")
    assert cli.main(["check", str(tmp_path)]) == 0
    out = capsys.readouterr()
    assert "warning: " in out.err and "1 with warnings" in out.out
    assert cli.main(["check", "--strict", str(tmp_path)]) == 1


def test_crlf_warns_and_strict_still_refuses_it(tmp_path, capsys):
    write(tmp_path, "crlf.csv", b"a,b\r\n1,2\r\n")
    assert cli.main(["check", str(tmp_path)]) == 0
    assert "CRLF" in capsys.readouterr().err
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


def test_fmt_check_github_is_an_annotation(tmp_path, capsys):
    """#219: `--fmt-check` printed its line plain under `--format github`."""
    p = tmp_path / "fmt.mdtbl"
    p.write_text("| id |  n |\n| --- | --- |\n| r_1 | 1 |\n")
    assert cli.main(["check", "--fmt-check", "--format", "github", str(p)]) == 1
    assert capsys.readouterr().err == (
        f"::error file={p},title=rowspec::not in canonical form (run --fmt)\n"
    )
    assert cli.main(["check", "--fmt-check", str(p)]) == 1
    assert capsys.readouterr().err == f"{p}: not in canonical form (run --fmt)\n"
