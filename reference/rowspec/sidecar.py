# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The sidecar: what a CSV cannot say about itself.

A CSV file carries a header row and nothing else. Which column is the row's
identity, and which column determines row order, are facts the format has no
place to put -- so `.mdtbl` puts them in declarations below the table, and an
ordinary CSV puts them in a small adjacent file.

Format is JSON, not TOML, for one reason: the sidecar is read by every
independent implementation, and JSON is in more standard libraries than TOML
is (Go, JavaScript, Python, Java, Ruby; TOML is stdlib only in Python 3.11+).
`reference/` is standard-library-only precisely so that the dependency budget
of an independent implementation stays at zero, and the sidecar inherits that
rule.

Two locations, distinguished by filename and never by content:

    data.csv.rowspec.json   declarations for data.csv
    .rowspec.json           a map of glob -> declarations, for that directory

The per-file form sorts next to its data file and can never collide with a
`data.json` that already exists. The directory form exists because a reference
registry has fifty CSVs keyed the same way and fifty sidecars is a reason not
to adopt.

Everything is optional. With no sidecar at all the validator still runs every
check that CSV can support on its own; the sidecar only buys the checks that
need a declared key or a declared order.
"""

import difflib
import fnmatch
import json
import os
import re
import unicodedata

from .table import Malformed, _quote, _spell, _window

SUFFIX = ".rowspec.json"
DIR_NAME = ".rowspec.json"

TYPES = ("number", "date", "text")
FIELDS = ("key", "order", "order_type", "columns", "delimiter")


class Sidecar:
    """A parsed declaration set. `path` is the file it came from, for errors."""

    def __init__(self, path, key=None, order=None, order_type=None, columns=None, delimiter=None):
        self.path = path
        self.key = key
        self.order = order
        self.order_type = order_type
        self.columns = columns or {}
        self.delimiter = delimiter

    def __repr__(self):  # pragma: no cover - debugging aid
        return f"Sidecar({self.path!r}, key={self.key!r}, order={self.order!r})"


def _no_duplicate_keys(pairs):
    """SPEC.md §9.4 -- a duplicate `key` or `order` declaration is refused.

    JSON's own duplicate-object-key rule is "last one wins", which is exactly
    the silent-overwrite the refusal exists to prevent, so the sidecar reader
    refuses instead of taking the last.
    """
    out = {}
    for k, v in pairs:
        if k in out:
            raise Malformed(f"duplicate declaration {k!r}")
        out[k] = v
    return out


def _suggest(name, known):
    near = difflib.get_close_matches(name, known, n=1, cutoff=0.6)
    return f"; did you mean {near[0]!r}?" if near else ""


def _validate(obj, where):
    """SPEC.md §9.12 -- a malformed declaration is refused, never ignored."""
    if not isinstance(obj, dict):
        raise Malformed(f"{where}: declarations must be a JSON object")
    for k in obj:
        if k not in FIELDS:
            raise Malformed(f"{where}: unknown declaration {k!r}{_suggest(k, FIELDS)}")
    # Each member is a string, and a non-string is told what that string is.
    must_be = {
        "key": "a column name",
        "order": "a column name",
        "order_type": f"one of the strings {', '.join(map(repr, TYPES[:-1]))} or {TYPES[-1]!r}",
        "delimiter": "a string of one Unicode scalar value",
    }
    for k, want in must_be.items():
        if k in obj and not isinstance(obj[k], str):
            raise Malformed(f"{where}: {k!r} must be {want}, not {type(obj[k]).__name__}")
    if "order_type" in obj and obj["order_type"] not in TYPES:
        raise Malformed(
            f"{where}: order_type {obj['order_type']!r} is not one of "
            f"{', '.join(TYPES)}{_suggest(obj['order_type'], TYPES)}"
        )
    if "delimiter" in obj:
        d = obj["delimiter"]
        # SPEC.md §13: one Unicode scalar value, so not a lone surrogate, which
        # JSON's `\ud800` escape produces as a one-character Python string.
        if len(d) != 1 or 0xD800 <= ord(d) <= 0xDFFF:
            raise Malformed(f"{where}: delimiter must be one Unicode scalar value, not {d!r}")
        if d in '"\r\n':
            raise Malformed(
                f"{where}: delimiter {d!r} is reserved: RFC 4180 uses it to quote a field "
                f"or to end a record, so the record boundaries would be undefined"
            )
    cols = obj.get("columns", {})
    if not isinstance(cols, dict):
        raise Malformed(f"{where}: 'columns' must be a JSON object of name -> type")
    for name, t in cols.items():
        if t not in TYPES:
            raise Malformed(
                f"{where}: column {name!r} declares type {t!r}, not one of "
                f"{', '.join(TYPES)}{_suggest(str(t), TYPES)}"
            )
    named = {}
    for name in cols:
        # SPEC.md §13: two members naming one column are refused as a repeated
        # member is, or the last of them would silently win.
        col = column_name(name)
        if col in named:
            raise Malformed(
                f"{where}: 'columns' names column {col!r} twice, "
                f"as {ascii(named[col])} and {ascii(name)}"
            )
        named[col] = name
    if "order" in obj and "key" not in obj:
        raise Malformed(
            f"{where}: 'order' requires 'key'. Without a key, rows with the same "
            f"order value fall back to their position in the file, which is a coordinate"
        )
    if "order_type" in obj and "order" not in obj:
        # SPEC.md §13: a declared check with no column to run on is refused,
        # since ignoring it would leave the author believing it ran.
        raise Malformed(
            f"{where}: 'order_type' requires 'order'. It declares the type of the "
            f"order column, and with no 'order' there is no column to check"
        )
    return obj


def _undecodable_line(path):
    """The first line holding a byte that is not UTF-8, quoted, never an
    offset (#216). `surrogateescape` decodes such a byte to a lone
    surrogate, which valid UTF-8 never gives, and the quote spells it
    `\\xNN`. A long line is shown from just before that byte."""
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8", "surrogateescape")
    bad = re.compile("[\udc80-\udcff]")
    line = next(ln for ln in text.split("\n") if bad.search(ln)).rstrip("\r")
    return _quote_at(line, bad.search(line).start())


def _quote_at(line, at):
    """`line` quoted as `_show` quotes it, each byte `surrogateescape` kept
    spelled `\\xNN` and a literal backslash spelled `\\\\`, so `\\xe9` in
    the quote is always a byte and never four characters of text (#239).
    It is shown from just before `at` when the text shown before it is
    long. The window is measured on the shown text, not the raw line, so a
    character `_show` spells out, such as U+200B as `\\u200b`, cannot push
    `at` past the end of the quote, and it is cut between characters, so
    no escape is shown in part."""

    return _quote(_window(_spell(line[:at])) + _spell(line[at:]), 60)


def _read(path):
    try:
        text = open(path, encoding="utf-8").read()
    except UnicodeDecodeError as e:
        raise Malformed(
            f"{os.path.basename(path)} is not valid UTF-8: the line "
            f"{_undecodable_line(path)} holds byte 0x{e.object[e.start]:02X}, which is "
            f"not part of a valid sequence ({e.reason})"
        ) from None
    try:
        return json.loads(text, object_pairs_hook=_no_duplicate_keys)
    except Malformed as e:
        raise Malformed(f"{os.path.basename(path)}: {e}") from None
    except json.JSONDecodeError as e:
        raise Malformed(
            f"{os.path.basename(path)} is not valid JSON: "
            f"{e.msg.removesuffix(' at')} {_where_json_stops(e)}"
        ) from None


def _where_json_stops(e):
    """Where a JSON parse stopped, by content, never by line number (#232):
    the line it stopped in, quoted, from just before that point when the
    line is long, or the end of the file when there is no line to quote.
    Some of the parser's messages end in "at", as in "Invalid control
    character at", and `_read` drops that word, since what follows here
    is not a position."""
    # JSON's whitespace only (RFC 8259 §2), so a form feed or a no-break
    # space after the stop is quoted rather than read as the end.
    if not e.doc[e.pos :].strip(" \t\n\r"):
        return "at the end of the file"
    # `_read` opens the file in text mode, so a CRLF is already a LF here.
    line = e.doc.split("\n")[e.lineno - 1]
    return f"in the line {_quote_at(line, e.colno - 1)}"


def find(data_path):
    """The sidecar for `data_path`, or None. Raises Malformed if one exists
    but does not parse -- an unreadable declaration is refused, never skipped,
    because skipping it silently downgrades the checks the file asked for."""
    per_file = data_path + SUFFIX
    if os.path.exists(per_file):
        obj = _validate(_read(per_file), os.path.basename(per_file))
        return _build(per_file, obj)
    shared = os.path.join(os.path.dirname(data_path) or ".", DIR_NAME)
    if os.path.exists(shared):
        table = _read(shared)
        if not isinstance(table, dict):
            raise Malformed(f"{DIR_NAME}: must be a JSON object of glob -> declarations")
        # Every entry's declarations are validated, not only the one that
        # applies, so a malformed entry for another file is reported rather
        # than left to wait for the one file that would reach it. A key is
        # matched against a basename, so one holding a path separator can
        # never apply and is refused rather than ignored.
        for p in table:
            if "/" in p or "\\" in p:
                raise Malformed(
                    f"{DIR_NAME}: entry {p!r} holds a path separator, so it can never "
                    f"match a file. Entries match file names in this directory only"
                )
        table = {p: _validate(obj, f"{DIR_NAME} [{p}]") for p, obj in table.items()}
        base = os.path.basename(data_path)
        # An entry naming the file exactly wins over any glob. Without one,
        # more than one matching glob is refused: picking one by position is
        # the silent choice that hid an exact entry listed after a glob (#190).
        # Both steps are case-sensitive on every host: `fnmatchcase`, because
        # `fnmatch` folds case on Windows while `in` never does.
        if base in table:
            return _build(shared, table[base])
        matches = [p for p in table if fnmatch.fnmatchcase(base, p)]
        if len(matches) > 1:
            raise Malformed(
                f"{DIR_NAME}: {base!r} matches more than one glob, "
                f"{', '.join(repr(p) for p in matches)}, and none is chosen by "
                f"position. Add an entry naming {base!r} exactly, or narrow the globs"
            )
        if matches:
            return _build(shared, table[matches[0]])
    return None


def column_name(name):
    """SPEC.md §13: a sidecar names a column as §9.2 compares names in CSV
    mode, after trimming ASCII space and tab only and after NFC. So `" id"`
    names `id`, and `""` names a column whose header cell is empty."""
    return unicodedata.normalize("NFC", name.strip(" \t"))


def _build(path, obj):
    names = {k: column_name(obj[k]) for k in ("key", "order") if k in obj}
    cols = {column_name(n): t for n, t in (obj.get("columns") or {}).items()}
    return Sidecar(
        path,
        key=names.get("key"),
        order=names.get("order"),
        order_type=obj.get("order_type"),
        columns=cols,
        delimiter=obj.get("delimiter"),
    )
