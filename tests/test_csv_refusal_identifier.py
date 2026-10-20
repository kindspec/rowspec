# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Every CSV-mode refusal carries its SPEC.md §9 identifier (#103).

SPEC.md §13 reads each refusal of the CSV profile as a §9 entry and says
which. Each test here drives one refusal path of `csvmode.py` or
`sidecar.py` and asserts the identifier §13 gives it: on every refusing
`Finding`, and on the `Malformed` raised for a file that cannot be read at
all. A warning carries none. These are unit tests of the reference; the
conformance cases for the profile live in conformance/cases-csv/ and are
written from SPEC.md by someone else.
"""

import json
import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import cli  # noqa: E402
from rowspec.csvmode import REFUSALS, check_file  # noqa: E402
from rowspec.table import Malformed  # noqa: E402


def _check(tmp_path, data, side=None, name="input.csv"):
    p = tmp_path / name
    p.write_bytes(data)
    if side is not None:
        raw = side if isinstance(side, bytes) else json.dumps(side).encode()
        (tmp_path / (name + ".rowspec.json")).write_bytes(raw)
    return check_file(str(p))


def _refusals(tmp_path, data, side=None):
    """The identifiers of the refusals reported, and the internal rules."""
    findings = _check(tmp_path, data, side)
    refused = [f for f in findings if f.level == "refuse"]
    assert refused, [str(f) for f in findings]
    return {f.refusal for f in refused}, {f.rule for f in refused}


ID = {"key": "id"}

#: (test id, input.csv, sidecar or None, the internal rule, §13's identifier).
#: The rule is asserted too, so each row is known to reach the path it names.
FINDINGS = [
    ("conflict-marker", b"a,b\n1,2\n<<<<<<< HEAD\n", None,
     "conflict-marker", "conflict-marker"),
    ("conflict-marker-in-a-quoted-field", b'a,b\n"x\n=======\ny",2\n', None,
     "conflict-marker", "conflict-marker"),
    ("duplicate-column", b"a,a\n1,2\n", None, "duplicate-column", "duplicate-column"),
    ("two-empty-header-cells", b",,a\n1,2,3\n", None, "duplicate-column", "duplicate-column"),
    # §13: a header of only blank cells is a header of one name, repeated,
    # not a missing header row.
    ("three-empty-header-cells", b",,\n1,2,3\n", None, "duplicate-column", "duplicate-column"),
    ("space-and-tab-header-cells", b" ,\t\n1,2\n", None, "duplicate-column",
     "duplicate-column"),
    ("two-empty-header-cells-over-a-no-break-space", b",\na,a\xc2\xa0\n", None,
     "duplicate-column", "duplicate-column"),
    ("grouped-header", b"g,g,g,h,h,h\na,b,c,d,e,f\n1,2,3,4,5,6\n", None,
     "grouped-header", "duplicate-column"),
    ("cf-in-a-column-name", b"a\xe2\x80\x8bb,c\n1,2\n", None,
     "invisible-in-name", "bad-identifier"),
    ("empty-key-value", b"id,n\n,1\n", ID, "key-not-identifier", "bad-identifier"),
    ("whitespace-in-a-key-value", b"id,n\na b,1\n", ID, "key-not-identifier", "bad-identifier"),
    ("cf-in-a-key-value", b"id,n\na\xe2\x80\x8bb,1\n", ID, "key-not-identifier", "bad-identifier"),
    ("field-count", b"a,b\n1,2,3\n", None, "field-count", "row-field-count"),
    ("empty-line-between-rows", b"a,b\n1,2\n\n3,4\n", None, "field-count", "row-field-count"),
    ("unterminated-quote", b'a,b\n1,"2\n', None, "unterminated-quote", "row-field-count"),
    ("stray-quote-in-an-unquoted-field", b'a,b\n1,2"3\n', None, "stray-quote", "row-field-count"),
    ("text-after-a-closing-quote", b'a,b\n1,"2"3\n', None, "stray-quote", "row-field-count"),
    ("duplicate-key", b"id,n\nr1,1\nr1,2\n", ID, "duplicate-key", "duplicate-row-id"),
    ("order-blank", b"id,n\nr1,1\nr2,\n", {"key": "id", "order": "n"},
     "order-blank", "bad-order-column"),
    ("order-mixed-types", b"id,n\nr1,1\nr2,x\n", {"key": "id", "order": "n"},
     "order-mixed-types", "bad-order-column"),
    ("order-infinite-number", b"id,n\nr1,1\nr2," + b"9" * 400 + b"\n",
     {"key": "id", "order": "n"}, "order-non-finite", "bad-order-column"),
    ("order-non-finite-spelling", b"id,n\nr1,a\nr2,-inf\n", {"key": "id", "order": "n"},
     "order-non-finite", "bad-order-column"),
    ("column-type", b"id,n\nr1,x\n", {"columns": {"n": "number"}},
     "column-type", "column-type-mismatch"),
    ("order-type", b"id,n\nr1,1\nr2,2\n", {"key": "id", "order": "n", "order_type": "text"},
     "order-type-mismatch", "column-type-mismatch"),
]  # fmt: skip


@pytest.mark.parametrize(
    "data, side, rule, refusal", [f[1:] for f in FINDINGS], ids=[f[0] for f in FINDINGS]
)
def test_a_refusing_finding_carries_its_identifier(tmp_path, data, side, rule, refusal):
    assert _refusals(tmp_path, data, side) == ({refusal}, {rule})


@pytest.mark.parametrize(
    "name, data, side",
    [
        ("one-tab.tsv", b"\t\n", None),
        ("two-tabs.tsv", b"\t\t\n", None),
        ("tab-header-over-a-tab-row.tsv", b"\t\n\t\n", None),
        ("one-space.csv", b" \n", {"delimiter": " "}),
    ],
)
def test_blank_cells_split_by_a_tab_or_space_delimiter_are_duplicate_columns(
    tmp_path, name, data, side
):
    """§13: each blank header cell is a column name, all one name, so a
    header of them is §9.2, not an empty file, even when the delimiter is
    itself a space or a tab."""
    p = tmp_path / name
    p.write_bytes(data)
    if side is not None:
        (tmp_path / (name + ".rowspec.json")).write_text(json.dumps(side))
    findings = check_file(str(p))
    assert {f.refusal for f in findings if f.level == "refuse"} == {"duplicate-column"}


def test_every_finding_rule_is_driven_above():
    """A rule added to `REFUSALS` without a row here is a path nothing pins."""
    assert {f[3] for f in FINDINGS} == set(REFUSALS)


def test_the_more_line_of_a_capped_list_carries_the_identifier(tmp_path):
    """Past `MAX_EXAMPLES` the rest are one "… and N more" refusal, which is
    still a refusal and so still carries the identifier."""
    findings = _check(tmp_path, b"a,b\n1\n2\n3\n4\n5\n")
    assert [f.message for f in findings][-1].startswith("… and 2 more")
    assert {f.refusal for f in findings} == {"row-field-count"}


def test_duplicate_key_more_line_carries_the_identifier(tmp_path):
    data = b"id\n" + b"".join(b"r%d\nr%d\n" % (i, i) for i in range(5))
    findings = _check(tmp_path, data, ID)
    assert findings[-1].message.startswith("… and 2 more")
    assert {f.refusal for f in findings} == {"duplicate-row-id"}


def test_order_mixed_types_under_order_type_meets_a_listed_entry(tmp_path):
    """§13: an order column of mixed types under an `order_type` meets both
    §9.10 and §9.27, and every refusal reported is one of them."""
    side = {"key": "id", "order": "n", "order_type": "number"}
    got, _ = _refusals(tmp_path, b"id,n\nr1,1\nr2,x\n", side)
    assert got and got <= {"bad-order-column", "column-type-mismatch"}


#: (test id, input.csv, sidecar or None, §13's identifier, a word of the message)
#: for every `Malformed` CSV mode raises for a per-file sidecar and its CSV.
#: The word pins the raise the row reaches, since one identifier has many.
RAISES = [
    # csvmode.py
    ("csv-not-utf8", b"a,b\n1,\xff\n", None, "bad-encoding", "not valid UTF-8"),
    ("csv-empty", b"", None, "no-table", "the file is empty"),
    ("csv-only-line-breaks", b"\n\r\n \t\n", None, "no-table", "the file is empty"),
    ("csv-first-line-empty", b"\na,b\n1,2\n", None, "no-table", "there is no header row"),
    ("csv-first-record-one-blank-field", b" \t\na\n", None, "no-table",
     "there is no header row"),
    ("key-names-no-column", b"a\n1\n", {"key": "id"}, "malformed-declaration", "declares key"),
    ("columns-names-no-column", b"a\n1\n", {"columns": {"b": "text"}},
     "malformed-declaration", "declares a type"),
    ("order-names-no-column", b"id\nr1\n", {"key": "id", "order": "n"},
     "bad-order-column", "declares order by"),
    # sidecar.py
    ("sidecar-repeated-member", b"id\nr1\n", b'{"key": "id", "key": "id"}',
     "duplicate-declaration", "duplicate declaration"),
    ("sidecar-repeated-member-in-columns", b"id\nr1\n",
     b'{"columns": {"id": "text", "id": "text"}}', "duplicate-declaration",
     "duplicate declaration"),
    ("sidecar-columns-names-one-column-twice", b"id\nr1\n",
     {"columns": {"id": "text", " id": "text"}}, "duplicate-declaration", "twice"),
    ("sidecar-not-an-object", b"id\nr1\n", ["key"], "malformed-declaration",
     "must be a JSON object"),
    ("sidecar-null", b"id\nr1\n", b"null", "malformed-declaration", "must be a JSON object"),
    ("sidecar-unknown-member", b"id\nr1\n", {"oder": "id"}, "malformed-declaration",
     "unknown declaration"),
    ("sidecar-key-not-a-string", b"id\nr1\n", {"key": 1}, "malformed-declaration",
     "'key' must be"),
    ("sidecar-order-not-a-string", b"id\nr1\n", {"key": "id", "order": None},
     "malformed-declaration", "'order' must be"),
    ("sidecar-order-type-not-a-string", b"id\nr1\n",
     {"key": "id", "order": "id", "order_type": 1}, "malformed-declaration",
     "'order_type' must be"),
    ("sidecar-delimiter-not-a-string", b"id\nr1\n", {"delimiter": 59},
     "malformed-declaration", "'delimiter' must be"),
    ("sidecar-order-type-unknown", b"id\nr1\n",
     {"key": "id", "order": "id", "order_type": "Number"}, "malformed-declaration",
     "is not one of"),
    ("sidecar-delimiter-two-scalars", b"id\nr1\n", {"delimiter": ";;"},
     "malformed-declaration", "one Unicode scalar value"),
    ("sidecar-delimiter-empty", b"id\nr1\n", {"delimiter": ""},
     "malformed-declaration", "one Unicode scalar value"),
    ("sidecar-delimiter-lone-surrogate", b"id\nr1\n", b'{"delimiter": "\\ud800"}',
     "malformed-declaration", "one Unicode scalar value"),
    ("sidecar-delimiter-reserved", b"id\nr1\n", {"delimiter": '"'},
     "malformed-declaration", "is reserved"),
    ("sidecar-columns-not-an-object", b"id\nr1\n", {"columns": ["id"]},
     "malformed-declaration", "'columns' must be"),
    ("sidecar-columns-unknown-type", b"id\nr1\n", {"columns": {"id": "int"}},
     "malformed-declaration", "declares type"),
    ("sidecar-columns-type-not-a-string", b"id\nr1\n", {"columns": {"id": 1}},
     "malformed-declaration", "declares type"),
    ("sidecar-order-without-key", b"id\nr1\n", {"order": "id"}, "order-without-key",
     "'order' requires 'key'"),
    ("sidecar-order-type-without-order", b"id\nr1\n", {"order_type": "text"},
     "malformed-declaration", "'order_type' requires 'order'"),
    ("sidecar-not-utf8", b"id\nr1\n", b'{"key": "i\xffd"}', "bad-encoding",
     "not valid UTF-8"),
    ("sidecar-utf16-with-a-bom", b"id\nr1\n", '﻿{"key": "id"}'.encode("utf-16-le"),
     "bad-encoding", "not valid UTF-8"),
    ("sidecar-utf16-without-a-bom", b"id\nr1\n", '{"key": "id"}'.encode("utf-16-le"),
     "malformed-declaration", "not valid JSON"),
    ("sidecar-not-json", b"id\nr1\n", b"{key: id}", "malformed-declaration", "not valid JSON"),
    ("sidecar-empty", b"id\nr1\n", b"", "malformed-declaration", "not valid JSON"),
    ("sidecar-leading-utf8-bom", b"id\nr1\n", b'\xef\xbb\xbf{"key": "id"}',
     "malformed-declaration", "not valid JSON"),
]  # fmt: skip


@pytest.mark.parametrize(
    "data, side, refusal, word", [r[1:] for r in RAISES], ids=[r[0] for r in RAISES]
)
def test_a_file_that_cannot_be_read_carries_its_identifier(tmp_path, data, side, refusal, word):
    with pytest.raises(Malformed) as e:
        _check(tmp_path, data, side)
    assert word in str(e.value), str(e.value)
    assert e.value.refusal == refusal


@pytest.mark.parametrize(
    "data",
    [b"\xef\xbb\xbfa,b\n1,2\n", b"a,b\r\n1,2\r\n", b"a,b\n1,2\r3,4\n"],
    ids=["bom", "crlf", "lone-cr"],
)
def test_a_warning_carries_no_identifier(tmp_path, data):
    findings = _check(tmp_path, data)
    assert findings and all(f.level == "warn" for f in findings), [str(f) for f in findings]
    assert {f.refusal for f in findings} == {None}


# --- the directory-level `.rowspec.json` -------------------------------------
# SPEC.md §13 defines the per-file sidecar only, so the three refusals that
# exist only for the directory form carry no identifier. An entry's own
# declarations are validated as a per-file sidecar's are, and carry the
# identifier §13 gives that refusal.


def _dir_check(tmp_path, table, data=b"id\nr1\n"):
    raw = table if isinstance(table, bytes) else json.dumps(table).encode()
    (tmp_path / ".rowspec.json").write_bytes(raw)
    p = tmp_path / "data.csv"
    p.write_bytes(data)
    return check_file(str(p))


@pytest.mark.parametrize(
    "table, word",
    [
        (["key"], "glob -> declarations"),
        ({"sub/*.csv": {"key": "id"}}, "path separator"),
        ({"*.csv": {"key": "id"}, "d*": {"key": "id"}}, "more than one glob"),
    ],
    ids=["not-an-object", "path-separator", "two-globs"],
)
def test_a_directory_form_refusal_carries_no_identifier(tmp_path, table, word):
    with pytest.raises(Malformed) as e:
        _dir_check(tmp_path, table)
    assert word in str(e.value), str(e.value)
    assert e.value.refusal is None


@pytest.mark.parametrize(
    "table, refusal",
    [
        ({"*.csv": {"oder": "id"}}, "malformed-declaration"),
        ({"*.csv": {"order": "id"}}, "order-without-key"),
        (b'{"*.csv": {"key": "id", "key": "id"}}', "duplicate-declaration"),
        (b"{", "malformed-declaration"),
    ],
    ids=["unknown-member", "order-without-key", "repeated-member", "not-json"],
)
def test_a_directory_form_entry_refusal_carries_the_sidecar_identifier(tmp_path, table, refusal):
    with pytest.raises(Malformed) as e:
        _dir_check(tmp_path, table)
    assert e.value.refusal == refusal


# --- the CLI ------------------------------------------------------------------


def test_check_prints_a_csv_finding_identifier(tmp_path, capsys):
    p = tmp_path / "dup.csv"
    p.write_bytes(b"id,n\nr1,1\nr1,2\n")
    (tmp_path / "dup.csv.rowspec.json").write_text('{"key": "id"}')
    assert cli.main(["check", str(p)]) == 1
    err = capsys.readouterr().err
    assert err.splitlines()[0] == f"{p}: duplicate key id='r1' — 2 rows share it [duplicate-row-id]"
    assert cli.main(["check", "--format", "github", str(p)]) == 1
    assert ",title=rowspec [duplicate-row-id]::duplicate key id='r1'" in capsys.readouterr().err


def test_check_prints_an_unreadable_csv_identifier(tmp_path, capsys):
    p = tmp_path / "empty.csv"
    p.write_bytes(b"")
    assert cli.main(["check", str(p)]) == 1
    assert capsys.readouterr().err == (
        f"{p}: file contains no table: the file is empty [no-table]\n"
    )
    assert cli.main(["check", "--format", "github", str(p)]) == 1
    assert ",title=rowspec [no-table]::file contains no table" in capsys.readouterr().err


def test_strict_prints_a_promoted_warning_without_an_identifier(tmp_path, capsys):
    """`--strict` is rowspec's option, not a §13 refusal, so a warning it
    promotes still has no §9 identifier to print."""
    p = tmp_path / "crlf.csv"
    p.write_bytes(b"a,b\r\n1,2\r\n")
    assert cli.main(["check", "--strict", str(p)]) == 1
    assert capsys.readouterr().err.splitlines()[0] == f"{p}: the file uses CRLF line endings"
