<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# CSV mode — the refusals, on a file nobody migrated

`rowspec check` runs SPEC.md §9 against the `.csv` you already have. No format
change, no sidecar, no configuration:

```sh
rowspec check data/
```

That alone refuses a committed conflict marker, a duplicate column name
(compared after Unicode NFC, so two headers that render identically are one
name), a row whose field count differs from the header, a file with no table,
a file that is not valid UTF-8, and an invisible format character inside a
column name.

Five lines of JSON next to the file buy the rest.

## The sidecar

```jsonc
// data/countries.csv.rowspec.json
{
  "key":   "code",          // the column holding the row identifier
  "order": "joined",        // the column that determines row order
  "order_type": "date",     // optional: number | date | text
  "columns": { "population": "number" },   // optional
  "delimiter": ","          // optional; .tsv is inferred
}
```

Everything is optional and the file itself is optional. Its only job is to say
what a CSV has nowhere to say.

**Why JSON and not TOML.** The sidecar is read by every independent
implementation of this spec, and JSON is in more standard libraries than TOML
is — Go, JavaScript, Java, Ruby and Python all parse it with nothing installed,
while TOML is stdlib only in Python 3.11 and later. `reference/` is
standard-library-only so an implementation's dependency budget stays at zero;
the sidecar inherits that rule. TOML's advantage is comments, and a `.jsonc`
comment survives no round trip, so the trade is comments against a dependency
in four languages.

**Why `<file>.rowspec.json` and not `<file>.rowspec` or `rowspec.toml`.**
Appending rather than replacing the extension means `data.csv` and
`data.csv.rowspec.json` sort next to each other, the sidecar can never collide
with a `data.json` that already exists in a data repository, and the `.json`
suffix makes editors, forges and JSON linters treat it correctly with no
configuration.

**One per directory, when one per file is too many.** A reference registry with
fifty CSVs keyed the same way should not need fifty sidecars, so a single
`.rowspec.json` in a directory maps globs to the same declarations:

```json
{
  "*.csv": { "key": "id" },
  "channels.csv": { "key": "id", "order": "launched", "order_type": "date" }
}
```

A per-file `<file>.rowspec.json` wins over the directory file. The two forms
are told apart by filename, never by inspecting content.

**A duplicate declaration is refused, not resolved.** JSON's own rule for a
repeated object key is last-one-wins, which is exactly the silent overwrite
SPEC.md §9.4 exists to prevent, so `{"key": "id", "key": "name"}` is an error.

## Which refusals apply

| SPEC.md §9 | | bare CSV | with sidecar | `.mdtbl` only |
| --- | --- | :-: | :-: | :-: |
| 1 | conflict markers | ● | | |
| 2 | duplicate column name | ● | | |
| 3 | duplicate aggregate name | | | ● |
| 4 | duplicate `key`/`order` declaration | | ● | |
| 5 | duplicate row id | | ● | |
| 6 | row field count ≠ header | ● | | |
| 7 | alignment row field count | | | ● |
| 8 | alignment-style row among data | | | ● |
| 9 | row-relative operator, no order | | | ● |
| 10 | `order` column absent or mixed-type | | ● | |
| 11 | unknown aggregate function | | | ● |
| 12 | malformed declaration | | ● | |
| 13 | no table | ● | | |

Four, four and five. §3's encoding rules add two more to the bare-CSV column —
invalid UTF-8, and a `Cf` format character inside a column name — for six
checks on a file with no declarations at all.

The five `.mdtbl`-only refusals are not a gap in CSV mode. Three of them are
about an alignment row and formulas, neither of which CSV has; two are about
aggregate declarations, which the sidecar deliberately does not grow. A CSV
with no computed column cannot violate them.

## Two warnings, not refusals

SPEC.md §3 requires LF and no BOM. In CSV mode both are **warnings**:

- **CRLF** is RFC 4180's own default line ending.
- **A UTF-8 BOM** is what Excel writes.

Measured: 71 of the 72 CSVs in `iptv-org/database` use CRLF. Refusing it would
reject a well-maintained public registry outright, and neither CRLF nor a BOM
can change a value once the BOM is stripped, which is the test SPEC.md §9 sets
for warning instead of refusing. `--strict` promotes both to refusals for a
repository that has already cleaned up.

## Errors name entities

```
data/channels.csv: duplicate key id='10.au' — 2 rows share it
data/channels.csv: row id='r_04' has 3 field(s), the header declares 4
data/countries.csv: unresolved conflict marker '<<<<<<< HEAD'
```

Never "error at line 7". A line number is wrong the moment anyone else edits
the file, and a pull-request reviewer cannot act on it; a key can be searched
for. When two entities render identically the message prints their codepoints,
because that is the only way to see the difference:

```
data/people.csv: duplicate key id='café' — 2 rows share it
    These ids render identically but are different bytes: 'café' = U+0063 U+0061
    U+0066 U+00E9  vs  'café' = U+0063 U+0061 U+0066 U+0065 U+0301. Unicode
    normalisation makes them one id, so one of these rows will be lost.
```

## CI

Copy [`docs/ci/rowspec-check.yml`](ci/rowspec-check.yml) into
`.github/workflows/`. A workflow file is the only repository-resident
configuration a forge executes: hooks are not cloned, and a merge driver needs
local config that never travels and is ignored by the bare repository the forge
actually merges in.
