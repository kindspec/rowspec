"""CSV mode: the specification's refusals, on a file nobody migrated.

The adoption claim of this project is that a maintainer with an ordinary
`data.csv` in an ordinary repository gets real checks with no format change and
no sidecar, and gets the rest by adding five lines of JSON next to the file.

Of the thirteen refusals in SPEC.md §9:

  * 1, 2, 6, 13 need nothing but the CSV, and §3's encoding rules add two more
    (invalid UTF-8, and format characters inside a column name);
  * 4, 5, 10, 12 need the sidecar, because they are about declarations and a
    CSV has nowhere to declare;
  * 3, 7, 8, 9, 11 cannot arise in a CSV -- they are about alignment rows,
    formulas and aggregates, none of which the format has.

Two deliberate softenings, both because refusing would reject data that is
correct. CRLF and a UTF-8 BOM are WARNINGS in CSV mode, not refusals: RFC 4180
makes CRLF the default line ending and Excel writes the BOM, so refusing either
would fail most of the corpus this mode exists to serve. Neither can change a
value, which is the test SPEC.md §9 sets for the warn-instead-of-refuse case.
"""

import csv
import io
import re
import sys
import unicodedata

from . import sidecar as sidecar_mod
from .table import Malformed

# Git writes exactly seven of its marker character, then a space and a label or
# end of line. `.mdtbl` refuses any line merely starting with those characters;
# a CSV cell can legitimately hold `<<<`, so CSV mode matches git's real output.
# `=======` alone is only a conflict if a `<<<<<<<` opened one, and git never
# emits it otherwise -- checking that ordering removes the one marker that
# plausibly occurs as data.
_MARKER = re.compile(r"^(<{7}|>{7}|\|{7}|={7})(?: (.*))?$")

# Deliberately not float(): Python accepts `1_0`, `nan`, `inf` and surrounding
# whitespace as numbers, and an independent implementation should not have to
# reproduce those quirks to agree with this one.
_NUMBER = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")
_DATE = re.compile(r"^\d{1,4}[-/]\d{1,2}[-/]\d{1,2}$")

MAX_EXAMPLES = 3


class Finding:
    """A refusal or a warning, named by the entity it is about."""

    def __init__(self, rule, message, detail=None, level="refuse"):
        self.rule = rule
        self.message = message
        self.detail = detail
        self.level = level

    def __str__(self):
        return self.message


def _warn(rule, message, detail=None):
    return Finding(rule, message, detail, level="warn")


def codepoints(s):
    return " ".join(f"U+{ord(c):04X}" for c in s)


def _show(s, limit=40):
    """A value as it should appear in an error: quoted, escaped, truncated."""
    s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    if len(s) > limit:
        s = s[: limit - 1] + "\u2026"
    return f"'{s}'"


def _type_of(v):
    if _DATE.match(v):
        return "date"
    if _NUMBER.match(v):
        return "number"
    return "text"


def _delimiter(path, side):
    if side is not None and side.delimiter:
        return side.delimiter
    return "\t" if path.lower().endswith((".tsv", ".tab")) else ","


def _decode(raw, name):
    """SPEC.md §3. Invalid UTF-8 is a refusal; a BOM is a warning, because
    Excel writes one and it cannot change a value once it is stripped."""
    warnings = []
    if raw.startswith(b"\xef\xbb\xbf"):
        warnings.append(
            _warn(
                "bom",
                f"{name} begins with a UTF-8 byte-order mark",
                "The BOM becomes part of the first column's name for any tool that does not "
                "strip it, so a script selecting that column by name silently gets nothing.",
            )
        )
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise Malformed(
            f"not valid UTF-8: byte 0x{raw[e.start]:02X} at offset {e.start} is not "
            f"part of a valid sequence ({e.reason})"
        ) from None
    return text, warnings


def _conflict_markers(text):
    """SPEC.md §9.1. Python's csv module parses a committed conflict as ordinary
    rows without complaint, which is why this check runs on the raw text."""
    out = []
    opened = False
    for line in text.splitlines():
        m = _MARKER.match(line)
        if not m:
            continue
        marker, label = m.group(1), m.group(2)
        if marker.startswith("<"):
            opened = True
        elif marker.startswith("=") and not opened:
            continue
        shown = f"{marker} {label}" if label else marker
        out.append(
            Finding(
                "conflict-marker",
                f"unresolved conflict marker {_show(shown, 60)}",
                "A merge was committed before it was finished. Every CSV reader in wide use, "
                "including Python's, parses these lines as ordinary data rows without "
                "complaining, so this file currently has rows nobody wrote.",
            )
        )
        if marker.startswith(">"):
            opened = False
    return out


def _grouped_header(names, second):
    """A spreadsheet export with a merged/grouped header: row 1 holds group
    labels repeated across their span, row 2 holds the real column names.

    Reporting that as fifty separate duplicate-column refusals is technically
    right and useless. Found on WHO's `cases.csv` in owid/covid-19-data, where
    'Europe' appears 51 times, and the maintainer needs to be told the SHAPE is
    wrong, not made to read fifty lines saying the same thing."""
    if len(names) < 6 or len(set(names)) > len(names) // 2:
        return None
    if second is None or len(second) != len(names):
        return None
    below = [c.strip() for c in second]
    if len(set(below)) != len(below) or sum(1 for c in below if c) < len(below) - 1:
        return None
    repeated = sorted({n for n in names if names.count(n) > 1 and n})
    return Finding(
        "grouped-header",
        f"the first row is not a row of column names: {_show(repeated[0])} and "
        f"{len(repeated) - 1} other label(s) repeat across {len(names)} columns, while "
        f"the row below holds {len(below)} distinct names",
        "This is a grouped or two-row header, the shape a spreadsheet produces from "
        "merged cells. There is no single row that names the columns, so no column can "
        "be referred to by name at all. Flatten it to one header row "
        "(for example 'Europe / France') before checking this file.",
    )


def _header_names(header, second=None):
    """SPEC.md §3: identifiers compare after NFC, and `Cf` format characters are
    rejected in them. SPEC.md §9.2: a duplicate column name is refused."""
    findings = []
    names = [unicodedata.normalize("NFC", h.strip()) for h in header]
    for name in names:
        for ch in name:
            if unicodedata.category(ch) == "Cf":
                findings.append(
                    Finding(
                        "invisible-in-name",
                        f"column name {_show(name)} contains the invisible character "
                        f"U+{ord(ch):04X} "
                        f"({unicodedata.name(ch, 'unnamed format character')})",
                        "It renders identically to the name without it but is a different "
                        "name, so a formula or a script that spells the name the obvious "
                        "way will never match this column.",
                    )
                )
                break
    seen = {}
    for i, name in enumerate(names):
        seen.setdefault(name, []).append(i)
    if len(seen) != len(names):
        grouped = _grouped_header(names, second)
        if grouped:
            return names, findings + [grouped]
    for name, idxs in seen.items():
        if len(idxs) == 1:
            continue
        forms = {header[i].strip() for i in idxs}
        label = _show(name) if name else "an unnamed column"
        if len(forms) > 1:
            detail = (
                "These header cells render identically but are different bytes: "
                + "  vs  ".join(f"{_show(f)} = {codepoints(f)}" for f in sorted(forms))
            )
        else:
            detail = (
                "Two columns with one name cannot be told apart by name, and every "
                "reference to that name is ambiguous."
            )
        findings.append(
            Finding(
                "duplicate-column",
                f"duplicate column name {label} \u2014 the header has {len(idxs)} of it",
                detail,
            )
        )
    return names, findings


def _name_row(rec, names, key_idx, n):
    """Name a row by an entity, never by a byte offset. The declared key first;
    the first field if there is no key; a record number only as a last resort,
    and labelled as a record so it is not mistaken for a line number -- a
    quoted field containing a newline makes those differ."""
    if key_idx is not None and key_idx < len(rec) and rec[key_idx].strip():
        return f"row {names[key_idx]}={_show(rec[key_idx].strip())}"
    if rec and names and rec[0].strip():
        return f"row {names[0]}={_show(rec[0].strip())}"
    return f"record {n}"


def _cap(findings, rule, items, render, detail):
    if not items:
        return
    for item in items[:MAX_EXAMPLES]:
        findings.append(Finding(rule, render(item), detail))
    if len(items) > MAX_EXAMPLES:
        findings.append(
            Finding(
                rule,
                f"\u2026 and {len(items) - MAX_EXAMPLES} more row(s) with the same problem",
                None,
            )
        )


def check_text(text, name="<input>", side=None, delimiter=","):
    """Every CSV-mode finding for already-decoded text. Raises Malformed only
    for the conditions that stop the file being read at all."""
    findings = list(_conflict_markers(text))
    if findings:
        # Everything downstream would be a consequence, not a finding: a
        # conflict block makes ragged rows and duplicate keys out of lines
        # nobody wrote. One clear cause beats twenty symptoms.
        return findings

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    records = [r for r in reader]
    if not records or not any(any(c.strip() for c in r) for r in records[:1]):
        # SPEC.md §9.13 -- a file containing no table.
        raise Malformed("file contains no table: there is no header row")
    header = records[0]
    names, name_findings = _header_names(header, records[1] if len(records) > 1 else None)
    findings += name_findings

    body = [r for r in records[1:] if r != []]

    key_idx = None
    if side and side.key:
        if side.key not in names:
            raise Malformed(
                f"{sidecar_mod.SUFFIX.lstrip('.')} declares key {_show(side.key)} but "
                f"{name} has no such column" + _near(side.key, names)
            )
        key_idx = names.index(side.key)

    # SPEC.md §9.6 -- a data row whose field count differs from the header.
    ragged = [(i, r) for i, r in enumerate(body, 1) if len(r) != len(header)]
    _cap(
        findings,
        "field-count",
        ragged,
        lambda ir: (
            f"{_name_row(ir[1], names, key_idx, ir[0])} has {len(ir[1])} field(s), "
            f"the header declares {len(header)}"
        ),
        "A row with the wrong number of fields silently shifts every value after the "
        "missing or extra comma into the wrong column. This is the check maintainers "
        "write by hand.",
    )

    if key_idx is not None:
        findings += _duplicate_keys(body, names, key_idx)

    if side:
        findings += _typed_columns(body, names, side, key_idx)
        findings += _order_column(body, names, side, key_idx)

    return findings


def _near(name, names):
    import difflib

    hit = difflib.get_close_matches(name, [n for n in names if n], n=1, cutoff=0.6)
    return f"; did you mean {_show(hit[0])}?" if hit else ""


def _duplicate_keys(body, names, key_idx):
    """SPEC.md §9.5. Compared after NFC, so two ids that render identically are
    the same id -- which is the point of normalising identifiers at all."""
    findings = []
    groups = {}
    for n, rec in enumerate(body, 1):
        raw = rec[key_idx].strip() if key_idx < len(rec) else ""
        groups.setdefault(unicodedata.normalize("NFC", raw), []).append((n, raw))
    key = names[key_idx]
    dups = [(k, v) for k, v in groups.items() if len(v) > 1]
    for k, occurrences in dups[:MAX_EXAMPLES]:
        forms = {raw for _, raw in occurrences}
        label = _show(k) if k else "the empty value"
        if len(forms) > 1:
            detail = (
                "These ids render identically but are different bytes: "
                + "  vs  ".join(f"{_show(f)} = {codepoints(f)}" for f in sorted(forms))
                + ". Unicode normalisation makes them one id, so one of these rows "
                "will be lost."
            )
        else:
            detail = (
                "A key must name exactly one row. When two rows share one, a merge can "
                "apply an edit to the wrong one and never report a conflict."
            )
        findings.append(
            Finding(
                "duplicate-key",
                f"duplicate key {key}={label} \u2014 {len(occurrences)} rows share it",
                detail,
            )
        )
    if len(dups) > MAX_EXAMPLES:
        findings.append(
            Finding(
                "duplicate-key",
                f"\u2026 and {len(dups) - MAX_EXAMPLES} more duplicated {key} value(s)",
            )
        )
    return findings


def _column_values(body, names, col):
    i = names.index(col)
    return [(n, rec[i].strip()) for n, rec in enumerate(body, 1) if i < len(rec)]


def _typed_columns(body, names, side, key_idx):
    """Beyond the thirteen: the declared type of a stored column. This is the
    check the hand-rolled registry validators were actually written to do."""
    findings = []
    for col, want in sorted(side.columns.items()):
        if col not in names:
            raise Malformed(
                f"{side.path.rsplit('/', 1)[-1]} declares a type for column {_show(col)} "
                f"but the file has no such column" + _near(col, names)
            )
        bad = [
            (n, v) for n, v in _column_values(body, names, col) if v != "" and _type_of(v) != want
        ]
        _cap(
            findings,
            "column-type",
            bad,
            lambda nv, col=col, want=want: (
                f"{_name_row(body[nv[0] - 1], names, key_idx, nv[0])} has "
                f"{col}={_show(nv[1])}, which is not a {want}"
            ),
            f"Column {_show(col)} is declared {want}. A value that does not coerce is an "
            f"error, never a zero and never a guess.",
        )
    return findings


def _order_column(body, names, side, key_idx):
    """SPEC.md §9.10 and §6: the order column must be a stored column with a
    single type across all rows, and must not contain a non-finite number."""
    findings = []
    col = side.order
    if not col:
        return findings
    if col not in names:
        raise Malformed(
            f"{side.path.rsplit('/', 1)[-1]} declares order by {_show(col)} but the file "
            f"has no such column" + _near(col, names)
        )
    values = [(n, v) for n, v in _column_values(body, names, col) if v != ""]
    kinds = {}
    for n, v in values:
        kinds.setdefault(_type_of(v), (n, v))
    if len(kinds) > 1:
        shown = ", ".join(
            f"{k} (e.g. {_name_row(body[n - 1], names, key_idx, n)} has {_show(v)})"
            for k, (n, v) in sorted(kinds.items())
        )
        findings.append(
            Finding(
                "order-mixed-types",
                f"order column {_show(col)} mixes types: {shown}",
                "A column with more than one type has no total order, so two "
                "implementations sorting by it can disagree about which row comes first.",
            )
        )
    elif side.order_type and kinds and side.order_type not in kinds:
        got = next(iter(kinds))
        n, v = kinds[got]
        findings.append(
            Finding(
                "order-type-mismatch",
                f"order column {_show(col)} is declared {side.order_type} but every value "
                f"reads as {got} (e.g. {_show(v)})",
                "Declaring the type turns an inference into a check. A column of "
                f"{got} sorts as {got}, which is not the order the declaration asks for.",
            )
        )
    if "number" in kinds:
        nonfinite = [(n, v) for n, v in values if _NUMBER.match(v) and not _finite(v)]
        _cap(
            findings,
            "order-non-finite",
            nonfinite,
            lambda nv: (
                f"order column {_show(col)} holds the non-finite value {_show(nv[1])} at "
                f"{_name_row(body[nv[0] - 1], names, key_idx, nv[0])}"
            ),
            "A non-finite number has no defined place in a sort.",
        )
    return findings


def _finite(v):
    try:
        f = float(v)
    except ValueError:
        return False
    return f == f and f not in (float("inf"), float("-inf"))


def check_file(path):
    """Findings for one CSV/TSV path. Refusals and warnings, in that order."""
    side = sidecar_mod.find(path)
    with open(path, "rb") as fh:
        raw = fh.read()
    if not raw.strip():
        raise Malformed("file contains no table: the file is empty")
    text, warnings = _decode(raw, "the file")
    if "\r\n" in text:
        warnings.append(
            _warn(
                "crlf",
                "the file uses CRLF line endings",
                "RFC 4180 makes CRLF the default for CSV, so this is not an error here, "
                "but it doubles the size of every diff on a platform that checks out LF.",
            )
        )
    findings = check_text(text, path, side, _delimiter(path, side))
    return findings + warnings


if __name__ == "__main__":  # pragma: no cover
    for p in sys.argv[1:]:
        for f in check_file(p):
            print(f"{p}: {f.level}: {f}")
