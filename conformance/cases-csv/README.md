<!-- SPDX-License-Identifier: CC0-1.0 -->
# The CSV-profile fixture tree

CC0. Copy it into any implementation, in any language. Everything a runner
needs is in the files; nothing is in Python.

SPEC.md §13 defines CSV mode as **a different profile, not a relaxation**: an
ordinary `.csv` checked against the subset of §9 that a delimiter-separated
file can violate. This tree is that profile's suite. `cases/` is the `.mdtbl`
profile's, and the two are separate trees because they are separate claims:
an implementation states which profile it conforms to, and runs every case of
each tree it claims.

## Shape

    cases-csv/<group>/<case-name>/
        expect.json              what to assert  (required; its presence IS the case)
        input.csv                the file under test, as exact bytes
        input.csv.rowspec.json   its sidecar, if the case needs one
        WHY.md                   prose, ignored by the runner

A directory is a case **iff** it contains `expect.json`. `kind` in
`expect.json` is authoritative; the parent directory name is a filing
convention, not an input.

The case directory is the repository root, as in `cases/`. The runner hands
the implementation the path of `input.csv` and nothing else; a sidecar is
found the way it would be in a real repository, by being the file beside it.
No `expect.json` field names either file.

## The sidecar

§13: refusal 5 (a duplicate row id) **requires a sidecar** declaring which
column is the key, because a CSV has nowhere to declare one. A case supplies
it as `input.csv.rowspec.json`, a JSON object:

```json
{ "key": "id" }
```

`key` names the column holding the row id. Without a sidecar there is no
declared key, and refusal 5 cannot apply.

§13 defines four more members, each optional: `order` names the column
that orders the rows and needs `key`, `order_type` declares its type and
needs `order`, `columns` maps column names to a declared type, and
`delimiter` names the field separator, one Unicode scalar value other than
`"`, CR or LF, which defaults to a comma for `input.csv`. A case uses them
as it uses `key`:

```json
{ "key": "id", "order": "joined", "order_type": "date",
  "columns": { "population": "number" } }
```

A member §13 does not define is refused, with no exception an
implementation may claim, so a case may assert that refusal portably.

**The per-file sidecar is the only form this profile uses.** rowspec's own
CSV mode also reads a directory-level `.rowspec.json` that maps filename globs
to declarations (`docs/csv.md`). That is a convenience of one implementation,
not part of the profile: no case here uses it, and an implementation claiming
the profile need not read it. It stays out because glob matching is not the
same across languages, or even across platforms: Python's own `fnmatch` is
case-insensitive on Windows and case-sensitive elsewhere. Cases about it would
test one library's matcher rather than SPEC.md.

## Kinds

| kind | fields | assertion |
| --- | --- | --- |
| `check` | `accept`, `refusal_contains`, `warns`, `warning_contains` | the file is refused, or accepted, or accepted with a warning §13 requires |

- `accept: false` with `refusal_contains`: the file is refused, and at least
  one refusal's message contains that substring.
- `accept: true`: the file is not refused, and nothing is asserted about
  warnings. This is the shape of a control case.
- `accept: true` with `warns: true`: the file is not refused and at least one
  warning is reported; `warning_contains` adds that one warning's message
  contains that substring. Assert a warning only where SPEC.md requires one:
  §13 makes refusals 26 (`leading-bom`) and 15 (`lone-cr`) warnings in CSV
  mode.

**There is no `warns: false`.** An implementation may report advisory warnings
the spec does not require, so "no warning" is not something the spec lets a
case check. The runner refuses `warns` with any value but `true`.

A refused file asserts nothing about warnings, and an accepted file has no
refusal to match, so `warns` or `warning_contains` on `accept: false`, and
`refusal_contains` on `accept: true`, are refused by the runner rather than
silently not checked. So is any field not in the table.

`refusal_contains: ""` means *refuse, for any stated reason*, and
`warning_contains: ""` means *warn, for any stated reason*. Use them where the
spec mandates the outcome and names no message: asserting invented wording
would test one implementation's phrasing rather than the profile.

A `refusal_contains: ""` case must be built so that exactly one refusal
applies, or it cannot tell which rule refused the file.

## Ground rules

- **Fixtures are exact bytes.** A byte-order mark, a CRLF, a lone CR or bytes
  that are not UTF-8 are each something a case may need to hold.
  `.gitattributes` disables end-of-line normalisation for this tree, and the
  runner reads `input.csv` as bytes. Never reformat a fixture.
- **A case may fail.** The suite is written from `SPEC.md` and runs ahead of
  any implementation; a failing case is a finding, not a bug in the case. Add,
  do not edit.

## Provenance

The first cases in this tree (#63) were written by an author who was not the
author of `reference/rowspec/csvmode.py`. They worked in a directory holding
only this export, with no `.git` and no implementation:

    git archive 436fd6f SPEC.md conformance ':(exclude)conformance/mutants.py'

`mutants.py` was left out because it quotes the implementation. The author
wrote 63 cases. The 57 here are byte for byte as written. The other six
expected a column name outside §4.1.9's allowlist to be refused, and were
withdrawn when SPEC.md §13 exempted CSV column names from it.

Where the spec left a question open, the author wrote the case their reading
supported, explained the reading in the case's `WHY.md`, and listed the
question. Their twelve, as they listed them:

1. **§9.14, a BOM against invalid UTF-8.** Only the BOM becomes a warning;
   invalid UTF-8 is still refused. (`encoding/invalid-utf8-refused`)
2. **Which refusals cannot apply in CSV.** Read as: 3, 4, 7–12, 17, 20–24 and
   the `.mdtbl` forms of 18 and 19 cannot apply; 1, 2, 5 (with a sidecar), 6,
   13 and 16 apply; 14 and 15 are warnings.
   (`nonapply/`, `nonapply/pipe-and-hash-values-accepted`)
3. **A formula-shaped header cell** is a column name, refused under §9.16.
   Withdrawn: SPEC.md §13 exempts CSV column names from §4.1.9's allowlist.
4. **A lone CR.** Inside a quoted field it warns. In a file whose lines all
   end in a lone CR, CR is read as the record break. No case for an unquoted
   lone CR mid-field. (`encoding/lone-cr-in-quoted-field-warns`,
   `encoding/lone-cr-line-breaks-warn`)
5. **Sidecar failure modes.** Invalid JSON, or a key naming a missing column,
   is refused; a duplicate `key` member is refused by analogy with §9.4. No
   case for a non-string key. (`identity/sidecar-*`)
6. **Malformed RFC 4180 quoting.** An unterminated quote is refused. No case
   for a bare quote inside an unquoted field, or for text after a closing
   quote. (`rfc4180/unterminated-quote-refused`)
7. **Blank and `#` lines are records**, refused on field count.
   (`fieldcount/blank-line-between-rows-refused`,
   `fieldcount/hash-line-is-a-record-refused`)
8. **A header-only CSV** is a zero-row table and is accepted; only a
   zero-byte file is "no table". (`table/header-only-accepted`,
   `table/empty-file-refused`)
9. **Identifiers compare after NFC**, with no case folding.
   (`columns/case-differing-columns-accepted`)
10. **Whitespace around fields.** No case.
11. **A conflict marker inside a quoted multi-line value.** No case.
12. **Key values are identifiers only when a sidecar declares the key.**
    (`ident/key-value-rules-without-sidecar-accepted`)

SPEC.md §13 has since settled some of these, each in the direction the
author read it or, where they wrote no case, by owner decision: all of 6 (an
unterminated quote, and since #96 a bare quote inside an unquoted field and
text after a closing quote, both refused), the blank line in 7, 11 (a marker
line is refused inside a quoted field too), and 12. It also withdrew 3.

§13's definition of the sidecar (#162) revised 2 and settled 5. On 2: the
sidecar's `order` brings §9.10 (`bad-order-column`) and §9.25
(`order-without-key`) into the profile, and a member repeated within the
sidecar is refused for §9.4's reason. §9.12 still does not apply, since a
sidecar is not a declaration line, but §13 refuses a sidecar name that names
no column in its own right. On 5: §13 now states every failure the reading
listed, and the case for a non-string `key` it left open: invalid JSON, a
sidecar that is not an object, a repeated member, and a name that is not a
string or names no column are each refused, by §13's text rather than by
analogy. The cases already written still read as before.

The rest stand as the cases read them.

SPEC.md §9.14 has since been split: malformed UTF-8 is still §9.14
(`bad-encoding`), and a leading BOM is now §9.26 (`leading-bom`). The cases'
`WHY.md` files keep the numbers they were written with.

The next 20 cases (#94) were written by a second author, also not the author
of `csvmode.py`, from this export and the text of #94, which lists in spec
terms the behaviours the first 57 cases left unpinned:

    git archive 6d6fd26 SPEC.md conformance ':(exclude)conformance/mutants.py'

They are byte for byte as written, and none was withdrawn. They cover the
three quoting faults of 6, the single and double trailing empty line, key
values trimmed of ASCII space and tab only, a quoted field after a lone CR,
and marker runs that do or do not start a line. Their `WHY.md` files record
no new open question.

The `columns/*-empty-name*` cases (#92) were written by an author who was not the author of
`csvmode.py` and did not read it, from SPEC.md and the case tree, on a branch
from `d51f27a`: an empty column name repeated, including in the grouped
header shape `,x,,,,`, is a duplicate column (§9.2), and a single empty name
is accepted. `cases/README.md` records that batch's other cases.

The cases on how a column name is trimmed before §9.2 compares it (#118:
`columns/space-name-*`, `tab-name-*`, `padded-name-*` and `no-break-space-*`)
were written by an author who was not the author of `csvmode.py` and did not
read it, from SPEC.md at `32466e0` and the case trees. `cases/README.md`
records that batch's other cases.

Nine cases (`columns/all-non-ascii-space-names-accepted`,
`columns/all-empty-names-refused`, `columns/all-ascii-blank-names-refused`,
`columns/repeated-non-ascii-space-name-refused`,
`columns/em-space-name-and-empty-name-accepted`,
`columns/ideographic-space-suffix-is-a-distinct-name-accepted`,
`columns/tab-padded-name-and-bare-name-refused`,
`ident/key-value-leading-em-space-refused` and
`identity/duplicate-id-after-tab-trim-refused`) were written by an author
who was not the author of `csvmode.py` and did not read it, from SPEC.md at
`29edd7c` and the case trees. `cases/README.md` records that batch's other
cases.

Four cases (`columns/vertical-tab-only-name-accepted`,
`columns/form-feed-only-name-accepted`,
`columns/no-break-space-suffix-in-a-data-row-under-a-label-and-empty-header-accepted`
and
`columns/no-break-space-suffix-in-a-data-row-under-two-empty-names-refused`)
were written by an author who was not the author of `csvmode.py` and did not
read it, from SPEC.md at `7652865` and the case trees. `cases/README.md`
records that batch's other cases.

These cases were written by an author who was not the author of `csvmode.py`
and did not read it, against SPEC.md at `e2b121a` in a worktree of that
commit, opening only SPEC.md, AGENTS.md, CONTRIBUTING.md, the two case
trees, the case-count floors in `conformance/run_cases.py`, the `justfile`,
the test names in `tests/test_conformance.py`, and the lines of README.md,
ROADMAP.md and CHANGELOG.md that state those counts. They cover every member
and rule of the sidecar §13 defines, and are named exactly:

- The sidecar's structure, encoding and members, and how `key` names a
  column: `sidecar/empty-object-accepted`,
  `sidecar/undefined-member-refused`,
  `sidecar/member-name-in-another-case-refused`,
  `sidecar/repeated-order-member-refused`,
  `sidecar/repeated-member-spelled-with-an-escape-refused`,
  `sidecar/repeated-columns-member-refused`,
  `sidecar/repeated-name-inside-columns-refused`,
  `sidecar/repeated-delimiter-member-refused`, `sidecar/array-refused`,
  `sidecar/string-refused`, `sidecar/null-refused`,
  `sidecar/empty-file-refused`, `sidecar/leading-bom-refused`,
  `sidecar/utf16le-with-bom-refused`, `sidecar/utf32be-refused`,
  `sidecar/non-utf8-byte-in-a-name-refused`,
  `sidecar/key-name-padded-with-space-and-tab-accepted`,
  `sidecar/key-name-padded-with-space-and-tab-applies-refused`,
  `sidecar/key-name-with-a-trailing-no-break-space-refused`,
  `sidecar/key-name-in-nfd-names-an-nfc-header-accepted`,
  `sidecar/key-name-in-nfc-names-an-nfd-header-accepted`,
  `sidecar/empty-key-name-names-an-empty-header-cell-accepted`,
  `sidecar/empty-key-name-names-an-empty-header-cell-applies-refused`,
  `sidecar/empty-key-name-with-no-empty-header-cell-refused`,
  `sidecar/tab-key-name-names-a-header-cell-of-spaces-accepted`,
  `sidecar/key-not-a-string-refused` and `sidecar/key-null-refused`.
- `order` and `order_type`, signed non-finite spellings included:
  `order/number-column-accepted`, `order/without-key-refused`,
  `order/names-no-column-refused`, `order/not-a-string-refused`,
  `order/name-padded-accepted`, `order/empty-cell-refused`,
  `order/cell-of-spaces-refused`, `order/cell-of-a-tab-refused`,
  `order/no-break-space-cell-beside-text-accepted`,
  `order/no-break-space-padded-number-beside-numbers-refused`,
  `order/space-and-tab-padded-number-beside-numbers-accepted`,
  `order/numbers-and-text-refused`, `order/numbers-and-dates-refused`,
  `order/dates-in-both-separators-accepted`,
  `order/uncalendared-date-beside-dates-accepted`,
  `order/exponent-beside-numbers-refused`,
  `order/leading-plus-beside-numbers-refused`,
  `order/arabic-indic-digit-beside-numbers-refused`,
  `order/mixed-separator-date-beside-dates-refused`,
  `order/inf-beside-text-refused`, `order/nan-in-every-row-refused`,
  `order/four-hundred-digit-number-refused`,
  `order/negative-four-hundred-digit-number-refused`,
  `order/three-hundred-digit-number-accepted`, `order/header-only-accepted`,
  `order/only-minus-inf-refused`,
  `order/text-column-with-one-minus-inf-cell-refused`,
  `order/only-plus-nan-refused`,
  `order/text-column-with-one-plus-nan-cell-refused`,
  `order/only-minus-infinity-mixed-case-refused`,
  `order/text-column-with-one-minus-infinity-mixed-case-cell-refused`,
  `order/only-plus-inf-upper-case-refused`,
  `order/text-column-with-one-plus-inf-upper-case-cell-refused`,
  `order/text-column-with-a-double-minus-inf-cell-accepted`,
  `order/text-column-with-a-plus-minus-nan-cell-accepted`,
  `order/text-column-with-a-minus-info-cell-accepted`,
  `order/text-column-with-a-minus-space-inf-cell-accepted`,
  `order/order-type-number-accepted`,
  `order/order-type-date-over-dates-accepted`,
  `order/order-type-text-over-text-accepted`,
  `order/order-type-text-over-numbers-refused`,
  `order/order-type-number-over-dates-refused`,
  `order/order-type-unknown-string-refused`,
  `order/order-type-capitalised-refused`,
  `order/order-type-not-a-string-refused` and
  `order/order-type-without-order-refused`.
- `columns`: `types/number-column-accepted`,
  `types/number-column-with-text-refused`,
  `types/number-column-with-a-trailing-point-refused`,
  `types/number-column-with-inf-refused`,
  `types/number-column-with-signed-inf-refused`,
  `types/number-column-with-a-no-break-space-padded-number-refused`,
  `types/text-column-with-a-number-refused`,
  `types/text-column-with-a-date-refused`,
  `types/date-column-with-mixed-separators-refused`,
  `types/date-column-with-a-number-refused`,
  `types/text-column-with-inf-accepted`,
  `types/date-column-in-both-separators-accepted`,
  `types/number-column-with-blanks-accepted`,
  `types/number-column-with-a-four-hundred-digit-number-accepted`,
  `types/number-column-with-a-space-and-tab-padded-number-accepted`,
  `types/columns-not-an-object-refused`, `types/unknown-type-refused`,
  `types/type-not-a-string-refused`, `types/names-no-column-refused`,
  `types/two-names-for-one-column-nfc-and-nfd-refused`,
  `types/two-names-for-one-column-padded-and-bare-refused`,
  `types/name-padded-accepted`,
  `types/empty-name-names-an-empty-header-cell-accepted`,
  `types/empty-name-with-no-empty-header-cell-refused`,
  `types/empty-columns-object-accepted`,
  `types/key-column-typed-number-accepted`,
  `types/key-column-typed-number-with-text-ids-refused`,
  `types/order-column-typed-text-over-numbers-refused` and
  `types/order-column-typed-number-accepted`.
- `delimiter`: `delimiter/semicolon-accepted`,
  `delimiter/semicolon-applies-refused`, `delimiter/tab-accepted`,
  `delimiter/non-ascii-accepted`, `delimiter/astral-scalar-accepted`,
  `delimiter/astral-scalar-as-a-surrogate-pair-escape-accepted`,
  `delimiter/double-quote-refused`, `delimiter/cr-refused`,
  `delimiter/lf-refused`, `delimiter/empty-string-refused`,
  `delimiter/two-scalars-refused`, `delimiter/combining-sequence-refused`,
  `delimiter/not-a-string-refused`,
  `delimiter/lone-surrogate-escape-refused`,
  `delimiter/not-nfc-normalised-accepted` and
  `delimiter/feff-leading-is-a-bom-warns`.

Every fixture here is named `input.csv`, so §13's default of a tab for a
file named `.tsv` or `.tab` cannot be reached by this tree, and no case
tests it. Each refusing case's `WHY.md` says which rule is the only one the
file breaks, and what the bare `refusal_contains: ""` assertion does not
pin. `cases/README.md` records that batch's other cases.
