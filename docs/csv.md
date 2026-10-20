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
  "order_type": "date",     // optional, needs "order": number | date | text
  "columns": { "population": "number" },   // optional
  "delimiter": ","          // optional; tab for .tsv and .tab, in any case
}
```

Everything is optional and the file itself is optional, except that `order`
needs `key` and `order_type` needs `order`: each is refused without the
other. Its only job is to say what a CSV has nowhere to say.

SPEC.md §13 defines all five members as part of the CSV profile: how a value
is trimmed and typed, and what each one refuses. `delimiter` is one Unicode
scalar value other than `"`, CR or LF. Any other member is refused, so a
misspelt `oder` cannot switch a check off without a word.

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

Within the directory file, an entry naming the file exactly wins over any
glob, wherever it is listed, so `channels.csv` above gets its `order` check
and every other CSV gets `key` alone. A file that more than one glob matches,
with no exact entry, is refused, and the refusal names the file and the globs.
Taking the first match would be a silent choice by position, and that
choice is what once hid an exact entry listed after a glob. Both the exact
match and the glob match are case-sensitive on every host, Windows included,
so `Channels.csv` names neither `channels.csv` nor a glob matching it.

Every entry's declarations are validated whenever the directory file is
read, so a malformed entry refuses every file checked through that
directory file, not only the file it names. Keys are checked only for a
path separator: a key holding `/` or `\` is refused, because entries match
file names in this directory and such a key could never apply. A key that
differs from a file's name only in case, trailing space or Unicode
normalization is not refused. It simply matches nothing.

The directory form is rowspec's convenience and outside SPEC.md §13's CSV
profile, which uses the per-file sidecar only.

**A duplicate declaration is refused, not resolved.** JSON's own rule for a
repeated object key is last-one-wins, which is exactly the silent overwrite
SPEC.md §9.4 exists to prevent, so `{"key": "id", "key": "name"}` is an error.

## Which refusals apply

This table classifies refusals 1 to 13, 25 and 27 of SPEC.md §9, each by its
number and the identifier §9 gives it, and §9's list goes on past them. Of
the later entries this page covers §9.14 (`bad-encoding`) and part of §9.16
(below the table), and §9.26 (`leading-bom`) and §9.15 (`lone-cr`), which in
CSV mode are warnings (*Two warnings, not refusals*). The rest are not
classified here. SPEC.md §9 is the complete list, and §13 states the CSV
profile: what it cannot apply, and how it reads §9.16, RFC 4180's records and
§4.1.12's conflict markers.

| SPEC.md §9 | | bare CSV | with sidecar | `.mdtbl` only |
| --- | --- | :-: | :-: | :-: |
| 1 | `conflict-marker`: conflict markers | ● | | |
| 2 | `duplicate-column`: duplicate column name | ● | | |
| 3 | `duplicate-aggregate`: duplicate aggregate name | | | ● |
| 4 | `duplicate-declaration`: duplicate `key`/`order` declaration | | ● | |
| 5 | `duplicate-row-id`: duplicate row id | | ● | |
| 6 | `row-field-count`: row field count ≠ header | ● | | |
| 7 | `alignment-field-count`: alignment row field count | | | ● |
| 8 | `alignment-row-in-data`: alignment-style row among data | | | ● |
| 9 | `rowrel-without-order`: row-relative operator, no order | | | ● |
| 10 | `bad-order-column`: `order` column absent, mixed, blank or non-finite | | ● | |
| 11 | `unknown-aggregate`: unknown aggregate function | | | ● |
| 12 | `malformed-declaration`: malformed declaration | | ● | |
| 13 | `no-table`: no table | ● | | |
| 25 | `order-without-key`: `order` with no `key` | | ● | |
| 27 | `column-type-mismatch`: value not of its declared type | | ● | |

Four, six and five. §3's encoding rules add two more to the bare-CSV column —
invalid UTF-8, and a `Cf` format character inside a column name — for six
checks on a file with no declarations at all. Three rows read the CSV
differently from `.mdtbl`, as SPEC.md §13 states:

- **1, conflict markers**: §4.1.12 unchanged. A line whose first seven
  characters are seven `<`, `=`, `>` or `|` is refused wherever it appears,
  a bare `=======` included. A cell that merely holds such a run, after the
  first field, is data.
- **6, field count**: record boundaries are RFC 4180's. An empty line between
  rows is a record of one empty field, so it is refused against a wider
  header; one empty line at the very end of the file is accepted. A quoted
  field that the file ends inside is refused outright: a CSV reader would
  otherwise fold every later row into that one cell. So is a stray quote: a
  `"` inside a field that does not start with one, like `5" pipe`, or text
  after a closing quote, like `"a"b`. RFC 4180 §2 allows neither, and readers
  disagree about what such a field holds.
- **5, duplicate row id**: with a key declared, a key value is also refused
  when it is empty or holds whitespace or a `Cf` character, since any of those
  lets two ids render alike without being equal (§9.16). Only ASCII space and
  tab are trimmed first, so a leading or trailing NBSP is refused too.

**Column names are exempt from the rest of §9.16.** Its allowlist exists so a
name can be written in a formula, and a CSV has none, so `first name` and
`total (USD)` are fine. Only a `Cf` character is still refused in one, so two
CSV column names *can* look identical: `first name` with an NBSP is not the
same column as `first name` with a space, and nothing refuses it. Key values
are exempt from the allowlist for the same reason: `002RadioTV.do` is a real
registry id.

The five `.mdtbl`-only refusals are not a gap in CSV mode. Three of them are
about an alignment row and formulas, neither of which CSV has, and two are
about aggregate declarations, which the sidecar deliberately does not grow. A
CSV with no computed column cannot violate them.

**The sidecar is the profile's set of declarations**, so SPEC.md §13 reads a
sidecar that does not parse, or that declares what cannot be checked, as
§9.12 (`malformed-declaration`): invalid JSON, a member the profile does not
define, a name that is not a string, and a `key` or `columns` member naming
no column of the file. A sidecar `order` naming no column is §9.10, and a
sidecar whose bytes are not UTF-8 is §9.14 (`bad-encoding`). §9.27
(`column-type-mismatch`), a value that is not of the type `columns` or
`order_type` declares, has no `.mdtbl` form, since `.mdtbl` declares no
types. §13 lists
the identifier every CSV-mode refusal is reported with, and `rowspec check`
ends each refused line with it, as the sample output below shows. A warning
has none. The directory-level `.rowspec.json` is outside §13, so a refusal
only it can make, such as a file matching two globs, has none either.

## Two warnings, not refusals

SPEC.md §9 refuses a UTF-8 BOM (§9.26, `leading-bom`) and a lone `CR` (§9.15,
`lone-cr`). In CSV mode both are **warnings**, as SPEC.md §13 states:

- **A UTF-8 BOM** is what Excel writes, and it cannot change a value once it is
  stripped.
- **A lone `CR`** — a carriage return not followed by `LF` — ends a record for a
  CSV reader but not a line for git, so the rows on either side of it share one
  line in every diff and merge.

**CRLF is also a warning, but it is rowspec's advisory, not a spec rule.**
SPEC.md §3 accepts `LF` and `CRLF` alike, and RFC 4180 makes `CRLF` the default
for CSV. Measured: 71 of the 72 CSVs in `iptv-org/database` use it. CSV mode
warns because `CRLF` doubles the size of every diff on a platform that checks
out `LF`.

`--strict` promotes all three to refusals, for a repository that has already
cleaned up or that enforces `LF`.

## Errors name entities

```
data/channels.csv: duplicate key id='10.au' — 2 rows share it [duplicate-row-id]
data/channels.csv: row id='r_04' has 3 field(s), the header declares 4 [row-field-count]
data/countries.csv: unresolved conflict marker '<<<<<<< HEAD' [conflict-marker]
```

Never "error at line 7". A line number is wrong the moment anyone else edits
the file, and a pull-request reviewer cannot act on it; a key can be searched
for. When two entities render identically the message prints their codepoints,
because that is the only way to see the difference:

```
data/people.csv: duplicate key id='café' — 2 rows share it [duplicate-row-id]
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
