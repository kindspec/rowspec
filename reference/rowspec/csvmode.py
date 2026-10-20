# SPDX-License-Identifier: Apache-2.0 OR MIT
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

§13 also says how a CSV reads four rules: record boundaries are RFC 4180's
(an empty line between rows is a one-field record, one empty line at the end
is accepted, and a quote left open at the end of the file is refused); a
conflict marker is §4.1.12's line-start rule; and a declared key's values may
not be empty or hold whitespace or `Cf`. Column names are exempt from §9.16's
allowlist, apart from `Cf`, because it exists for formulas.

Two deliberate softenings, both stated by SPEC.md §13: refusals 26 (a UTF-8
BOM, `leading-bom`) and 15 (a lone CR, `lone-cr`) are WARNINGS in CSV mode,
not refusals. Excel writes the BOM, and refusing either would fail files whose
values are correct.

CRLF is a third warning, and it is rowspec's advisory rather than a spec rule:
SPEC.md §3 accepts LF and CRLF alike, and RFC 4180 makes CRLF the default for
CSV. It stays a warning so that `--strict` can refuse it for a repository
that enforces LF, which is what the action's `strict` input documents.
"""

import contextlib
import csv
import io
import re
import sys
import threading
import unicodedata

from rowspec import sidecar as sidecar_mod
from rowspec.table import (
    DATE_RE,
    Malformed,
    _escape,
    _isnum,
    _show,
    _show_bytes,
    is_nonfinite_spelling,
    split_lines,
)

# SPEC.md §4.1.12, as written and with no CSV exception: a line whose first
# seven characters are seven `<`, `=`, `>` or `|` is a conflict line wherever
# it appears. A shorter run, or one that does not start the line, is data.
_MARKER = re.compile(r"^(<{7}|>{7}|\|{7}|={7})")

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


def _type_of(v):
    """SPEC.md §4.1.6 and §4.1.7, by the recognisers `table.py` uses for
    `.mdtbl`: ASCII digits only, no `+`, exponent or one-sided point, and one
    separator per date. `fullmatch`, because `DATE_RE` ends in `$`, which
    also matches before a final LF, and a quoted CSV field can end in one."""
    if DATE_RE.fullmatch(v):
        return "date"
    if _isnum(v):
        return "number"
    return "text"


def _delimiter(path, side):
    if side is not None and side.delimiter:
        return side.delimiter
    return "\t" if path.lower().endswith((".tsv", ".tab")) else ","


#: What `surrogateescape` decodes a byte that is not UTF-8 to. Valid UTF-8
#: never decodes to a lone surrogate, so one of these is such a byte.
_UNDECODED = re.compile("[\udc80-\udcff]")


#: The largest `csv.field_size_limit` every platform takes. Python 3.11 and
#: 3.12 store it in a C long, which is 32 bits on Windows; 3.13 stores it in
#: a C ssize_t. 2**31 - 1 fits both on every platform.
_FIELD_LIMIT = 2**31 - 1

#: Held while the limit is lifted. The limit is one value for the whole
#: process, so two overlapping checks in two threads would otherwise put it
#: back out of order: the second would read the first's restored default
#: and crash, and the lifted limit would outlive them both. Re-entrant, so
#: a lifted call may make another. It orders rowspec's own calls only:
#: other code using `csv` while a check runs still sees the lifted limit.
_FIELD_LIMIT_LOCK = threading.RLock()


@contextlib.contextmanager
def _no_field_limit():
    """Lift the csv module's field size limit, 131,072 characters by
    default, while CSV mode reads a file (#235). SPEC.md sets no limit on a
    field and §9 has no refusal for a long one, so a reader-imposed limit
    would turn a file the specification accepts into a crash. The old
    limit is put back after, because it is process-wide state."""
    with _FIELD_LIMIT_LOCK:
        old = csv.field_size_limit(_FIELD_LIMIT)
        try:
            yield
        finally:
            csv.field_size_limit(old)


@_no_field_limit()
def _undecodable(raw, delimiter, key):
    """Where the first byte that is not UTF-8 sits, by entity, never by
    offset (#216): the header row, or the row as `_name_row` names it, and
    the field holding the byte, each such byte spelled `\\xNN`. A long field
    is shown from just before that byte, so the quote cannot cut it off.
    Records the csv module cannot read, such as a field over its size
    limit, leave only the file to name."""
    text = raw.decode("utf-8", "surrogateescape")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    names = []
    try:
        for n, rec in enumerate(reader):
            bad = next((f for f in rec if _UNDECODED.search(f)), None)
            if n == 0:
                names = [unicodedata.normalize("NFC", h.strip(" \t")) for h in rec]
            if bad is None:
                continue
            at = _UNDECODED.search(bad).start()
            if at > 20:
                bad = "\u2026" + bad[at - 10 :]
            # `_show_bytes`, not `_show`: a literal backslash is spelled `\\\\`
            # so `\\xNN` is always a byte, and no `\\xNN` is cut in half (#242).
            field = _show_bytes(bad)
            if n == 0:
                return f"the header row: the field {field}"
            key_idx = next((i for i, h in enumerate(names) if h == key), None)
            return f"{_name_row(rec, names, key_idx, n, _show_bytes)}: the field {field}"
    except csv.Error:
        pass
    return "the file"


def _decode(raw, name, delimiter=",", key=None):
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
            f"{_undecodable(raw, delimiter, key)} is not valid UTF-8: byte "
            f"0x{raw[e.start]:02X} is not part of a valid sequence ({e.reason})"
        ) from None
    return text, warnings


def _conflict_markers(text):
    """SPEC.md §9.1. Python's csv module parses a committed conflict as ordinary
    rows without complaint, which is why this check runs on the raw text."""
    out = []
    for line in split_lines(text):
        if not _MARKER.match(line):
            continue
        out.append(
            Finding(
                "conflict-marker",
                f"unresolved conflict marker {_show(line, 60)}",
                "A merge was committed before it was finished. Every CSV reader in wide use, "
                "including Python's, parses these lines as ordinary data rows without "
                "complaining, so this file currently has rows nobody wrote.",
            )
        )
    return out


def _quote_faults(text, delimiter):
    """RFC 4180 §2's quoting, as SPEC.md §13 reads it. Returns `(opened,
    stray, where)`: the start of a quoted field still open at the end of the
    file, or None; the start of each field holding a stray quote; and, for
    each of those starts, `(record number, start of that record)`, so the
    finding can name the row rather than an offset.

    A field that opens with `"` runs to the next `"` that is not doubled. If
    the file ends first, the grammar generates no records from there on, and
    Python's csv module folds the rest of the file into one cell, so every
    later row vanishes into a value.

    A stray quote is a `"` inside a field that did not open with one (rule
    5), or anything but the delimiter or a line break after a closing quote.
    The csv module reads both without complaint, and what the field then
    holds is that module's guess.

    The scan is left to the `re` engine (#93): `run` matches well-formed
    fields, and Python looks only at a field it stops at. It uses no
    possessive quantifier, which CPython before 3.11.5 can match wrongly
    (gh-106052), and its one group repeat is bounded, because the engine
    keeps backtracking state for every iteration of one.
    """
    if '"' not in text:
        return None, [], {}
    seps = delimiter + "\r\n"
    ends = re.escape(seps)
    # A quoted field holding no `""`, or an unquoted one, and what ends it.
    run = re.compile(rf'(?:(?:"[^"]*"|[^"{ends}]*)[{ends}]){{0,{_RUN_FIELDS}}}')
    unquoted = re.compile(rf'[^"{ends}]*')
    rest = re.compile(rf"[^{ends}]*")
    stray, where, rec, rec_start, counted, pos, n = [], {}, 1, 0, 0, 0, len(text)
    while True:
        start = run.match(text, pos).end()
        if start == n:
            return None, stray, where
        if text[start] == '"':
            end = _closing(text, start)
            if end < 0:
                return text[start : start + 20], stray, where
        else:
            end = unquoted.match(text, start).end()
        if end == n:
            return None, stray, where
        if text[end] in seps:
            # Well formed: a quoted field holding `""`, or `run`'s bound.
            pos = end
            continue
        # A quote inside an unquoted field, or anything after a closing quote.
        rec, rec_start = _records(text, counted, start, rec, rec_start)
        stray.append(start)
        where[start] = (rec, rec_start)
        pos = counted = rest.match(text, end).end()


#: Fields per `run` match in `_quote_faults`: enough that Python's share of
#: the loop is negligible, few enough that the engine's state stays small.
_RUN_FIELDS = 4096
_QUOTES = re.compile('"*')


def _closing(text, i):
    """Just past the quote that closes the quoted field opening at `i`, or
    -1 if the text ends first. Inside the field a run of quotes of even
    length is that many halves of `""`; an odd run's last quote closes it."""
    while True:
        i = text.find('"', i + 1)
        if i < 0:
            return -1
        j = _QUOTES.match(text, i).end()
        if (j - i) % 2:
            return j
        i = j - 1


def _records(text, i, stop, rec, rec_start):
    """`(rec, rec_start)` advanced over the record boundaries in
    `text[i:stop]` that are outside quoted fields. `i` is a field start or
    the line break or delimiter before one, and every field up to `stop`
    is well formed."""
    while i < stop:
        q = text.find('"', i, stop)
        end = stop if q < 0 else q
        rec += text.count("\n", i, end) + text.count("\r", i, end) - text.count("\r\n", i, end)
        br = max(text.rfind("\r", i, end), text.rfind("\n", i, end))
        if br >= 0:
            rec_start = br + 1
        if q < 0:
            break
        i = _closing(text, q)
    return rec, rec_start


def _field_text(text, start, delimiter):
    """The raw text of the field that starts at `start`, up to the delimiter
    or line break that ends it -- quoted part, stray text and all."""
    i, quoted = start, False
    while i < len(text):
        ch = text[i]
        if quoted and ch == '"':
            if text.startswith('""', i):
                i += 2
                continue
            quoted = False
        elif ch == '"' and i == start:
            quoted = True
        elif not quoted and (ch == delimiter or ch in "\r\n"):
            break
        i += 1
    return text[start:i]


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
    below = [c.strip(" \t") for c in second]
    if len(set(below)) != len(below) or sum(1 for c in below if c) < len(below) - 1:
        return None
    repeated = sorted({n for n in names if names.count(n) > 1 and n})
    if not repeated:
        # Only empty names repeat. SPEC.md §13 makes an empty header cell a
        # column name, so this is §9.2's duplicate column, not a group label.
        return None
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
    rejected in them. SPEC.md §9.2: a duplicate column name is refused.

    SPEC.md §13: a name is trimmed of ASCII space and tab only, as a key value is
    (§4.1.4), so a leading or trailing non-ASCII space is part of the name."""
    findings = []
    names = [unicodedata.normalize("NFC", h.strip(" \t")) for h in header]
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
        forms = {header[i].strip(" \t") for i in idxs}
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


def _name_row(rec, names, key_idx, n, show=_show):
    """Name a row by an entity, never by a byte offset. The declared key first;
    the first field if there is no key; a record number only as a last resort,
    and labelled as a record so it is not mistaken for a line number -- a
    quoted field containing a newline makes those differ."""
    # §13: a key value is trimmed of ASCII space and tab only, so `a<U+00A0>`
    # is named as itself and not as the row `a`.
    key = rec[key_idx].strip(" \t") if key_idx is not None and key_idx < len(rec) else ""
    if key:
        return f"row {_escape(names[key_idx])}={show(key)}"
    first = rec[0].strip(" \t") if rec else ""
    if first and names:
        return f"row {_escape(names[0])}={show(first)}"
    return f"record {n}"


def _cap(findings, rule, items, render, detail, unit="row(s)"):
    if not items:
        return
    for item in items[:MAX_EXAMPLES]:
        findings.append(Finding(rule, render(item), detail))
    if len(items) > MAX_EXAMPLES:
        findings.append(
            Finding(
                rule,
                f"\u2026 and {len(items) - MAX_EXAMPLES} more {unit} with the same problem",
                None,
            )
        )


@_no_field_limit()
def check_text(text, name="<input>", side=None, delimiter=","):
    """Every CSV-mode finding for already-decoded text. Raises Malformed only
    for the conditions that stop the file being read at all."""
    findings = list(_conflict_markers(text))
    if findings:
        # Everything downstream would be a consequence, not a finding: a
        # conflict block makes ragged rows and duplicate keys out of lines
        # nobody wrote. One clear cause beats twenty symptoms.
        return findings

    # SPEC.md §13 and RFC 4180 -- a quoted field still open at the end of the
    # file, or a stray quote. Refused alone, for the conflict marker's reason:
    # every finding after it would be about rows the csv module had to guess.
    opened, stray, where = _quote_faults(text, delimiter)
    if opened is not None:
        return [
            Finding(
                "unterminated-quote",
                f"the quoted field that starts {_show(opened)} is never closed",
                "RFC 4180 ends a quoted field at its closing quote. With none before the "
                "end of the file, a CSV reader folds every later row into this one cell, "
                "so those rows silently disappear.",
            )
        ]
    if stray:

        def first_record(at):
            reader = csv.reader(io.StringIO(text[at:], newline=""), delimiter=delimiter)
            return next(reader, [])

        names = [unicodedata.normalize("NFC", h.strip(" \t")) for h in first_record(0)]
        # The first column of that name, as `names.index` gives elsewhere.
        key_idx = next((i for i, n in enumerate(names) if side and n == side.key), None)

        def locate(start):
            rec, rec_start = where[start]
            if rec == 1:
                return "the header row"
            return _name_row(first_record(rec_start), names, key_idx, rec - 1)

        stray_findings = []
        _cap(
            stray_findings,
            "stray-quote",
            stray,
            lambda s: (
                f"{locate(s)}: the field {_show(_field_text(text, s, delimiter))} "
                f"holds a stray quote"
            ),
            "RFC 4180 allows a quote only to open a field, to close it, or doubled "
            "inside a quoted field. Anywhere else a CSV reader has to guess what the "
            "field holds, and readers guess differently.",
            unit="field(s)",
        )
        return stray_findings

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    records = [r for r in reader]
    if not records or not any(any(c.strip(" \t") for c in r) for r in records[:1]):
        # SPEC.md §9.13 -- a file containing no table. §13 trims a name of
        # ASCII space and tab only, so a U+00A0 header cell is a name.
        raise Malformed("file contains no table: there is no header row")
    header = records[0]
    names, name_findings = _header_names(header, records[1] if len(records) > 1 else None)
    findings += name_findings

    # RFC 4180: an empty line is a record of one empty field, not a gap. The
    # csv module yields `[]` for it; skipping that made the record count
    # depend on the reader, so it is read as `[""]` and the field-count rule
    # decides, as for any other row. SPEC.md §13 accepts ONE empty line at the
    # end of the file: it is not between rows, and real exports end that way.
    rest = records[1:-1] if len(records) > 1 and records[-1] == [] else records[1:]
    body = [r if r else [""] for r in rest]

    key_idx = None
    if side and side.key is not None:
        if side.key not in names:
            raise Malformed(
                f"{side.path.rsplit('/', 1)[-1]} declares key {_show(side.key)} but "
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
        findings += _key_identifiers(body, names, key_idx)
        findings += _duplicate_keys(body, names, key_idx)

    if side:
        findings += _typed_columns(body, names, side, key_idx)
        findings += _order_column(body, names, side, key_idx)

    return findings


def _near(name, names):
    import difflib

    hit = difflib.get_close_matches(name, [n for n in names if n], n=1, cutoff=0.6)
    return f"; did you mean {_show(hit[0])}?" if hit else ""


def _key_identifiers(body, names, key_idx):
    """SPEC.md §13: a value of the declared key column is refused when it is
    empty, or holds whitespace or a `Cf` format character (§4.1.9, §9.16).
    An id that renders like another without being equal to it is the
    duplicate-key refusal failing to fire, and that is true of any key.

    The rest of §4.1.9's allowlist is not applied. It exists so a name can be
    written inside a formula, and a CSV has none: `002RadioTV.do` and
    `Africa/Abidjan` are real registry keys."""
    key = _escape(names[key_idx])
    bad = []
    for n, rec in enumerate(body, 1):
        if key_idx >= len(rec):
            continue  # a short row is the field-count refusal's to report
        # §4.1.4 trims ASCII space and tab only; any other whitespace at
        # either end is part of the value, and is refused below.
        raw = unicodedata.normalize("NFC", rec[key_idx].strip(" \t"))
        if raw == "":
            bad.append((n, rec, f"{key} value is empty, and an id is one or more characters"))
            continue
        for ch in raw:
            if ch.isspace() or unicodedata.category(ch) == "Cf":
                kind = "whitespace" if ch.isspace() else "the format character"
                bad.append((n, rec, f"{key} value {_show(raw)} contains {kind} U+{ord(ch):04X}"))
                break
    findings = []
    _cap(
        findings,
        "key-not-identifier",
        bad,
        lambda b: f"{_name_row(b[1], names, key_idx, b[0])}: {b[2]}",
        "A key value names its row. One that is empty, or that holds a space or an "
        "invisible character, can render exactly like another id without being equal "
        "to it, and then no duplicate is ever found.",
    )
    return findings


def _duplicate_keys(body, names, key_idx):
    """SPEC.md §9.5. Compared after NFC, so two ids that render identically are
    the same id -- which is the point of normalising identifiers at all."""
    findings = []
    groups = {}
    for n, rec in enumerate(body, 1):
        raw = rec[key_idx].strip(" \t") if key_idx < len(rec) else ""
        groups.setdefault(unicodedata.normalize("NFC", raw), []).append((n, raw))
    key = _escape(names[key_idx])
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
    # §13 / §4.1.4: ASCII space and tab only, so `<U+00A0>5` stays text.
    return [(n, rec[i].strip(" \t")) for n, rec in enumerate(body, 1) if i < len(rec)]


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
    single type across all rows, blank in no row, and must not contain a
    non-finite number."""
    findings = []
    col = side.order
    if col is None:
        return findings
    if col not in names:
        raise Malformed(
            f"{side.path.rsplit('/', 1)[-1]} declares order by {_show(col)} but the file "
            f"has no such column" + _near(col, names)
        )
    # SPEC.md §13 and §9.10: blank is none of the three types, so an order
    # column blank in any row, a cell of spaces or tabs included, is refused.
    blank = [n for n, v in _column_values(body, names, col) if v == ""]
    _cap(
        findings,
        "order-blank",
        blank,
        lambda n: (
            f"order column {_show(col)} is blank at {_name_row(body[n - 1], names, key_idx, n)}"
        ),
        "An order needs a place for every row, and a blank value has none: it is "
        "neither a number, a date nor text, so implementations disagree about where "
        "that row sorts.",
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
        nonfinite = [(n, v) for n, v in values if _isnum(v) and not _finite(v)]
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
    # §9.10: a non-finite spelling is refused in any row, even in a column of
    # nothing else, where it is text and the column has one type.
    spelled = [(n, v) for n, v in values if is_nonfinite_spelling(v)]
    _cap(
        findings,
        "order-non-finite",
        spelled,
        lambda nv: (
            f"order column {_show(col)} holds the non-finite spelling {_show(nv[1])} at "
            f"{_name_row(body[nv[0] - 1], names, key_idx, nv[0])}"
        ),
        "SPEC.md §9.10 refuses inf, nan and infinity, in any case and with or without a "
        "sign, in an order column.",
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
    # ASCII space, tab and line breaks only: VT or FF alone is a column name.
    if not raw.strip(b" \t\r\n"):
        raise Malformed("file contains no table: the file is empty")
    text, warnings = _decode(raw, "the file", _delimiter(path, side), side and side.key)
    if "\r\n" in text:
        warnings.append(
            _warn(
                "crlf",
                "the file uses CRLF line endings",
                "SPEC.md §3 accepts CRLF and RFC 4180 makes it the default for CSV, so this "
                "is rowspec's advisory, not an error: it doubles the size of every diff on a "
                "platform that checks out LF.",
            )
        )
    if "\r" in text.replace("\r\n", ""):
        warnings.append(
            _warn(
                "lone-cr",
                "the file contains a lone CR (a carriage return not followed by LF)",
                "A CSV reader ends a record at a lone CR but git does not end a line there, "
                "so the rows on either side of it share one line in every diff and merge.",
            )
        )
    findings = check_text(text, path, side, _delimiter(path, side))
    return findings + warnings


if __name__ == "__main__":  # pragma: no cover
    for p in sys.argv[1:]:
        for f in check_file(p):
            print(f"{p}: {f.level}: {f}")
