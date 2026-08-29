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
import unicodedata

from .table import Malformed

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
    for k in ("key", "order", "order_type", "delimiter"):
        if k in obj and not isinstance(obj[k], str):
            raise Malformed(f"{where}: {k!r} must be a column name, not {type(obj[k]).__name__}")
    if "order_type" in obj and obj["order_type"] not in TYPES:
        raise Malformed(
            f"{where}: order_type {obj['order_type']!r} is not one of "
            f"{', '.join(TYPES)}{_suggest(obj['order_type'], TYPES)}"
        )
    if "delimiter" in obj and len(obj["delimiter"]) != 1:
        raise Malformed(f"{where}: delimiter must be a single character, not {obj['delimiter']!r}")
    cols = obj.get("columns", {})
    if not isinstance(cols, dict):
        raise Malformed(f"{where}: 'columns' must be a JSON object of name -> type")
    for name, t in cols.items():
        if t not in TYPES:
            raise Malformed(
                f"{where}: column {name!r} declares type {t!r}, not one of "
                f"{', '.join(TYPES)}{_suggest(str(t), TYPES)}"
            )
    if "order" in obj and "key" not in obj:
        raise Malformed(
            f"{where}: 'order' requires 'key'. Without a key, rows with the same "
            f"order value fall back to their position in the file, which is a coordinate"
        )
    return obj


def _read(path):
    try:
        text = open(path, encoding="utf-8").read()
    except UnicodeDecodeError as e:
        raise Malformed(f"{os.path.basename(path)} is not valid UTF-8: {e}") from None
    try:
        return json.loads(text, object_pairs_hook=_no_duplicate_keys)
    except Malformed as e:
        raise Malformed(f"{os.path.basename(path)}: {e}") from None
    except json.JSONDecodeError as e:
        raise Malformed(
            f"{os.path.basename(path)} is not valid JSON: {e.msg} (line {e.lineno})"
        ) from None


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
        base = os.path.basename(data_path)
        for pattern, obj in table.items():
            if fnmatch.fnmatch(base, pattern):
                obj = _validate(obj, f"{DIR_NAME} [{pattern}]")
                return _build(shared, obj)
    return None


def _build(path, obj):
    norm = {k: unicodedata.normalize("NFC", v) for k, v in obj.items() if isinstance(v, str)}
    cols = {unicodedata.normalize("NFC", n): t for n, t in (obj.get("columns") or {}).items()}
    return Sidecar(
        path,
        key=norm.get("key"),
        order=norm.get("order"),
        order_type=norm.get("order_type"),
        columns=cols,
        delimiter=obj.get("delimiter"),
    )
