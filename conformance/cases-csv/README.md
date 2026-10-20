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
case-insensitive on Windows and case-sensitive elsewhere (rowspec uses
`fnmatchcase`, case-sensitive on every host, for that reason). Cases about it
would test one library's matcher rather than SPEC.md.

## Kinds

| kind | fields | assertion |
| --- | --- | --- |
| `check` | `accept`, `refusal`, `refusal_contains`, `warns`, `warning_contains` | the file is refused, or accepted, or accepted with a warning §13 requires |

- `accept: false` with `refusal`: the file is refused, and every refusal
  reported carries a listed §9 identifier (below).
- `accept: false` with `refusal_contains`: the file is refused, and at least
  one refusal's message contains that substring. No case in this tree uses
  it any more. A refused case carries exactly one of the two fields.
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
`refusal` or `refusal_contains` on `accept: true`, are refused by the runner
rather than silently not checked. So is any field not in the table.

`refusal_contains: ""` means *refuse, for any stated reason*, and
`warning_contains: ""` means *warn, for any stated reason*. Use them where the
spec mandates the outcome and names no message: asserting invented wording
would test one implementation's phrasing rather than the profile.

A `refusal_contains: ""` case must be built so that exactly one refusal
applies, or it cannot tell which rule refused the file.

### Asserting the identifier

SPEC.md §13 requires every CSV-mode refusal to be reported with a §9
identifier, and says which entry each refusal of the profile is read as. A
refusing case asserts it with `refusal` in place of `refusal_contains`:

- `refusal` is the identifier that opens the refusal's entry in SPEC.md §9,
  such as `"row-field-count"`, or a list of every identifier that applies
  where the file meets more than one entry.
- **The case passes only when at least one refusal is reported and every
  refusal reported carries an identifier the case lists** (§13). CSV mode may
  report several refusals for one file, so an implementation that reports
  one of the listed refusals passes, and one that also refuses for an
  unlisted reason fails. Warnings are not refusals and are not checked
  against `refusal`.
- The message is never asserted on, as in `cases/`. A Python implementation
  reports the identifier as the `refusal` attribute of each refusing finding,
  and of the `Malformed` it raises for a file it cannot read at all; a runner
  in another language reads it from wherever that language's binding puts it.

Every refusing case here carries `refusal`. A runner that does not yet read
`refusal` (#103) cannot run this tree until it does. This repository's
runner also fails a refusal reported with no identifier under
`refusal_contains`, since §13 requires one on every refusal. Each refusing case's `WHY.md` ends with an
`## Identifier` section quoting the §13 reading and the §9 entry that decide
its list. The quotes are verbatim from SPEC.md except that markdown bold
markers are dropped.

## Counts

281 cases: 100 accepted and 181 refused, and every refused case carries
`refusal`.

134 refusing cases were converted from `refusal_contains: ""` to `refusal`,
and 56 cases were added: 46 refusing and 10 accepted. Of those, 46 (36
refusing, 10 accepted) were written against SPEC.md at `72f41cf`, and 10
refusing ones against the amendment at `df99ea1`, which classifies a
conflict line before records count as rows and makes §13's list of
malformed sidecars complete. No input or sidecar byte of an existing case
changed.

## Identifier to cases

"Sole" counts cases listing only that identifier; "with others" counts cases
listing it beside at least one more, marked `*` in the last column. §9
entries no CSV case can reach (`duplicate-aggregate`,
`alignment-field-count`, `alignment-row-in-data`, `rowrel-without-order`,
`unknown-aggregate`, `value-in-computed-cell`, `malformed-table-line`,
`unclassified-line`, `malformed-formula`, `bad-alignment-row`,
`computed-column-compared`, `nesting-too-deep`, `ident-compared-in-if`)
are left out, and so are `lone-cr` and `leading-bom`, which §13 makes
warnings.

| identifier | sole refusal | with others | cases |
| --- | --- | --- | --- |
| `conflict-marker` | 15 | 3 | `markers/diff3-base-marker-refused`, `markers/eight-ours-marker-chars-refused`, `markers/empty-line-then-only-a-conflict-record-refused`*, `markers/full-conflict-block-refused`, `markers/leading-marker-line-before-the-header-refused`, `markers/marker-inside-quoted-field-and-duplicate-column-refused`*, `markers/marker-inside-quoted-field-the-file-ends-inside-refused`*, `markers/marker-line-in-a-two-column-file-refused`, `markers/marker-line-inside-quoted-field-refused`, `markers/only-a-head-marker-refused`, `markers/only-conflict-lines-refused`, `markers/ours-marker-refused`, `markers/separator-marker-refused`, `markers/separator-marker-with-suffix-refused`, `markers/stray-quote-on-a-marker-line-refused`, `markers/theirs-marker-refused`, `markers/two-separator-lines-with-a-declared-key-refused`, `markers/unterminated-quote-opened-on-a-conflict-record-refused` |
| `duplicate-column` | 13 | 3 | `columns/all-ascii-blank-names-refused`, `columns/all-empty-names-refused`, `columns/cf-name-and-duplicate-name-refused`*, `columns/duplicate-column-after-nfc-refused`, `columns/duplicate-column-refused`, `columns/grouped-header-of-repeated-labels-refused`, `columns/no-break-space-suffix-in-a-data-row-under-two-empty-names-refused`, `columns/padded-name-and-bare-name-refused`, `columns/repeated-empty-name-refused`, `columns/repeated-non-ascii-space-name-refused`, `columns/space-name-and-empty-name-refused`, `columns/tab-name-and-empty-name-refused`, `columns/tab-padded-name-and-bare-name-refused`, `columns/two-empty-names-refused`, `fieldcount/duplicate-column-and-short-row-refused`*, `markers/marker-inside-quoted-field-and-duplicate-column-refused`* |
| `duplicate-declaration` | 8 | 1 | `identity/sidecar-duplicate-key-member-refused`, `sidecar/repeated-columns-member-refused`, `sidecar/repeated-delimiter-member-refused`, `sidecar/repeated-member-and-undefined-member-refused`*, `sidecar/repeated-member-spelled-with-an-escape-refused`, `sidecar/repeated-name-inside-columns-refused`, `sidecar/repeated-order-member-refused`, `types/two-names-for-one-column-nfc-and-nfd-refused`, `types/two-names-for-one-column-padded-and-bare-refused` |
| `duplicate-row-id` | 9 | 2 | `ident/key-value-with-space-repeated-refused`*, `identity/duplicate-id-after-nfc-refused`, `identity/duplicate-id-after-tab-trim-refused`, `identity/duplicate-id-beside-a-lone-cr-in-a-quoted-field-refused`, `identity/duplicate-id-in-a-file-with-a-leading-bom-refused`, `identity/duplicate-id-quoted-and-bare-refused`, `identity/duplicate-id-with-key-refused`, `identity/key-on-second-column-refused`, `sidecar/empty-key-name-names-an-empty-header-cell-applies-refused`, `sidecar/key-name-padded-with-space-and-tab-applies-refused`, `types/key-column-typed-number-with-repeated-text-ids-refused`* |
| `row-field-count` | 16 | 3 | `delimiter/semicolon-applies-refused`, `fieldcount/blank-line-between-rows-refused`, `fieldcount/duplicate-column-and-short-row-refused`*, `fieldcount/extra-field-refused`, `fieldcount/hash-line-is-a-record-refused`, `fieldcount/missing-field-refused`, `fieldcount/trailing-line-of-one-space-refused`, `fieldcount/two-trailing-empty-lines-refused`, `markers/empty-line-then-only-a-conflict-record-refused`*, `markers/marker-inside-quoted-field-the-file-ends-inside-refused`*, `markers/six-char-leading-run-is-the-header-refused`, `rfc4180/lone-cr-unterminated-quote-at-record-start-refused`, `rfc4180/quote-inside-unquoted-field-refused`, `rfc4180/quote-pair-inside-unquoted-field-refused`, `rfc4180/quoted-comma-is-one-field-refused`, `rfc4180/space-after-closing-quote-refused`, `rfc4180/text-after-closing-quote-refused`, `rfc4180/unterminated-quote-refused`, `rfc4180/unterminated-quote-with-escaped-quote-refused` |
| `bad-order-column` | 33 | 7 | `order/arabic-indic-digit-beside-numbers-refused`, `order/cell-of-a-tab-refused`, `order/cell-of-spaces-refused`, `order/empty-cell-refused`, `order/empty-name-names-an-empty-header-cell-with-inf-refused`, `order/empty-name-with-no-empty-header-cell-refused`, `order/exponent-beside-numbers-refused`, `order/four-hundred-digit-number-refused`, `order/inf-beside-text-refused`, `order/invalid-order-type-beside-an-order-naming-no-column-refused`*, `order/leading-plus-beside-numbers-refused`, `order/mixed-separator-date-beside-dates-refused`, `order/names-no-column-refused`, `order/nan-in-every-row-refused`, `order/negative-four-hundred-digit-number-refused`, `order/no-break-space-padded-number-beside-numbers-refused`, `order/numbers-and-dates-refused`, `order/numbers-and-text-refused`, `order/only-minus-inf-refused`, `order/only-minus-infinity-mixed-case-refused`, `order/only-plus-inf-upper-case-refused`, `order/only-plus-nan-refused`, `order/order-type-date-with-a-cell-of-spaces-refused`, `order/order-type-number-over-a-trailing-point-refused`*, `order/order-type-number-over-numbers-and-text-refused`*, `order/order-type-number-with-a-blank-cell-refused`, `order/order-type-number-with-a-four-hundred-digit-number-refused`, `order/order-type-number-with-inf-refused`*, `order/order-type-text-over-text-with-inf-refused`, `order/order-type-with-order-naming-no-column-refused`, `order/quoted-date-ending-in-lf-beside-a-date-refused`, `order/quoted-number-ending-in-lf-beside-a-number-refused`, `order/text-column-with-one-minus-inf-cell-refused`, `order/text-column-with-one-minus-infinity-mixed-case-cell-refused`, `order/text-column-with-one-plus-inf-upper-case-cell-refused`, `order/text-column-with-one-plus-nan-cell-refused`, `order/without-key-over-mixed-types-refused`*, `types/columns-member-naming-a-missing-order-column-refused`*, `types/order-column-typed-number-over-numbers-and-text-refused`*, `types/order-column-typed-number-with-a-blank-cell-refused` |
| `malformed-declaration` | 36 | 6 | `delimiter/combining-sequence-refused`, `delimiter/cr-refused`, `delimiter/double-quote-refused`, `delimiter/empty-string-refused`, `delimiter/lf-refused`, `delimiter/lone-surrogate-escape-refused`, `delimiter/not-a-string-refused`, `delimiter/two-scalars-refused`, `encoding/invalid-utf8-and-undefined-sidecar-member-refused`*, `identity/sidecar-invalid-json-refused`, `identity/sidecar-key-names-absent-column-refused`, `order/invalid-order-type-beside-an-order-naming-no-column-refused`*, `order/not-a-string-refused`, `order/order-type-capitalised-refused`, `order/order-type-not-a-string-refused`, `order/order-type-unknown-string-refused`, `order/order-type-without-order-refused`, `order/without-key-and-undefined-member-refused`*, `sidecar/array-refused`, `sidecar/empty-file-refused`, `sidecar/empty-key-name-with-no-empty-header-cell-refused`, `sidecar/key-name-one-byte-short-refused`, `sidecar/key-name-with-a-trailing-no-break-space-refused`, `sidecar/key-not-a-string-refused`, `sidecar/key-null-refused`, `sidecar/leading-bom-refused`, `sidecar/member-name-in-another-case-refused`, `sidecar/null-refused`, `sidecar/repeated-member-and-undefined-member-refused`*, `sidecar/string-refused`, `sidecar/trailing-comma-refused`, `sidecar/undefined-member-refused`, `sidecar/utf16le-without-bom-refused`, `sidecar/utf32be-refused`, `sidecar/utf32le-without-bom-refused`, `table/empty-file-with-a-key-sidecar-refused`*, `types/columns-member-naming-a-missing-order-column-refused`*, `types/columns-not-an-object-refused`, `types/empty-name-with-no-empty-header-cell-refused`, `types/names-no-column-refused`, `types/type-not-a-string-refused`, `types/unknown-type-refused` |
| `no-table` | 2 | 1 | `table/bom-only-file-refused`, `table/empty-file-refused`, `table/empty-file-with-a-key-sidecar-refused`* |
| `bad-encoding` | 7 | 1 | `encoding/invalid-utf8-and-undefined-sidecar-member-refused`*, `encoding/invalid-utf8-refused`, `encoding/leading-bom-and-invalid-utf8-refused`, `sidecar/non-utf8-byte-in-a-name-refused`, `sidecar/utf16be-with-bom-refused`, `sidecar/utf16le-with-bom-refused`, `sidecar/utf16le-without-bom-non-ascii-name-refused`, `sidecar/utf32le-with-bom-refused` |
| `bad-identifier` | 8 | 2 | `columns/cf-name-and-duplicate-name-refused`*, `ident/column-name-with-cf-refused`, `ident/column-name-with-interior-feff-refused`, `ident/key-value-empty-refused`, `ident/key-value-leading-em-space-refused`, `ident/key-value-leading-nbsp-refused`, `ident/key-value-trailing-ideographic-space-refused`, `ident/key-value-with-cf-refused`, `ident/key-value-with-space-refused`, `ident/key-value-with-space-repeated-refused`* |
| `order-without-key` | 1 | 2 | `order/without-key-and-undefined-member-refused`*, `order/without-key-over-mixed-types-refused`*, `order/without-key-refused` |
| `column-type-mismatch` | 15 | 5 | `order/order-type-number-over-a-trailing-point-refused`*, `order/order-type-number-over-dates-refused`, `order/order-type-number-over-numbers-and-text-refused`*, `order/order-type-number-with-inf-refused`*, `order/order-type-text-over-numbers-refused`, `order/order-type-text-over-one-number-refused`, `types/date-column-with-a-number-refused`, `types/date-column-with-a-quoted-date-ending-in-lf-refused`, `types/date-column-with-mixed-separators-refused`, `types/key-column-typed-number-with-repeated-text-ids-refused`*, `types/key-column-typed-number-with-text-ids-refused`, `types/number-column-with-a-no-break-space-padded-number-refused`, `types/number-column-with-a-trailing-point-refused`, `types/number-column-with-inf-refused`, `types/number-column-with-signed-inf-refused`, `types/number-column-with-text-refused`, `types/order-column-typed-number-over-numbers-and-text-refused`*, `types/order-column-typed-text-over-numbers-refused`, `types/text-column-with-a-date-refused`, `types/text-column-with-a-number-refused` |

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
analogy. The cases already written still read as before. Since #103, §13
reads the sidecar as the profile's set of declarations, so §9.12
(`malformed-declaration`) does apply to it, and names the identifier each
of these refusals is reported with.

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

Eight cases (#192) were written by an author who was not the author of
`csvmode.py` and did not read it, against SPEC.md at `5e992d8`, opening
only SPEC.md, AGENTS.md, CONTRIBUTING.md, this tree, the case-count floor
in `conformance/run_cases.py`, and the lines of ROADMAP.md and
CHANGELOG.md that state the count:

- A quoted value ending in LF keeps the LF, which §4.1.6's `number` and
  §4.1.7's `date` do not generate and ASCII space-and-tab trimming does not
  remove, so it is text:
  `order/quoted-date-ending-in-lf-beside-a-date-refused`,
  `order/quoted-number-ending-in-lf-beside-a-number-refused`,
  `order/quoted-dates-ending-in-lf-in-every-row-accepted`,
  `types/date-column-with-a-quoted-date-ending-in-lf-refused` and
  `types/text-column-with-a-quoted-date-ending-in-lf-accepted`.
- `"order": ""` names an empty-headed column, or no column:
  `order/empty-name-with-no-empty-header-cell-refused`,
  `order/empty-name-names-an-empty-header-cell-accepted` and
  `order/empty-name-names-an-empty-header-cell-with-inf-refused`.

Each `WHY.md` quotes the sentences of SPEC.md that decide it, and records
no new open question.

The identifier assertions (#103) were written from SPEC.md alone, by an
author who read no implementation: not `reference/`, not a second
implementation, not the runner, and no repository on disk or on GitHub.
They were written in two passes.

1. **Against rowspec `72f41cf`.** The inputs were four given files and
   nothing else: SPEC.md, this README, `case-body.schema.json`, and this
   tree as it stood. That pass converted 134 cases, added 46, and left two
   cases without `refusal`, because that text did not settle their
   identifiers.
2. **Against rowspec `df99ea1`**, an amendment to §13 that settles both of
   those cases. The inputs were the amended SPEC.md and its diff from
   `72f41cf`, and nothing else. That pass gave the two cases `refusal`,
   re-checked every case against the diff, and added 10 cases for the
   readings the amendment introduces. No other case's outcome or
   identifiers changed. Every quote from the first pass is still verbatim
   in `df99ea1`. Seven `markers/*` notes that described the old open
   question were rewritten.

Every `refusal` list is derived from §13's reading of each refusal as a §9
entry, and from §9's rule that a case names every identifier that applies.
No checker decided an outcome. The scripts that wrote the files checked
only that:

- each quoted sentence occurs in SPEC.md at `df99ea1`;
- no existing input byte changed;
- each `refusal` fits `case-body.schema.json`;
- each of the 14 one-byte twins differs from its pair by one byte.

`AMBIGUITIES.md` in this directory records the two settled questions, and
`DISPUTES.md` records that no existing verdict was disputed.

The amendment's files, by sha256:

    832a8568c6a1f54edb9c930bb806c45ac3077990fcfb6077853fc00f39df4a6e  given2/SPEC.md
    2e2c1a0566f70a1989a91c8fe71f5b5ff94caba9e591d200e9c0deb55622a080  given2/SPEC-72f41cf-to-new.diff

The first pass's given files, by sha256:

    762ba02a5080156c0e26d3b2aff8df6a777bf92883f77a801c2e27e72114829a  SPEC.md
    a591f98f047d069af7049379dfd28d7e0643083433bc8799105a911ffdd74f99  cases-csv-README.md
    13bf7b49b093bcf8766c9c767712d06449225263892fa73d38bd283662f399cc  case-body.schema.json

and each of the 799 files of the given tree, `conformance/cases-csv/`, is
listed with its sha256 in `GIVEN.sha256` in this directory, one line per
file in `sha256sum` format, sorted by path in the C locale. That manifest's
own sha256 is
`951595fc4684fccd4c065226148c3d810e5f3968c15b5880cf90a80534a6e90e`.

One case, `columns/grouped-header-of-repeated-labels-refused`, was added
from the code's coverage gap, not blind. Its author had read
`reference/rowspec/csvmode.py`, which reports a header of repeated labels
above a row of distinct names as a grouped header, and saw that no case
reached that path. CONTRIBUTING.md's rule that the suite is not written by
the implementation's author does not cover it. Its verdict and identifier
are derived from SPEC.md §13 and §9.2, which its `WHY.md` quotes, and not
from what the code does.
