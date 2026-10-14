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

`key` names the column holding the row id. It is the one declaration §13
calls for. Without a sidecar there is no declared key, and refusal 5 cannot
apply.

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
  §13 makes refusals 14 (a BOM) and 15 (a lone CR) warnings in CSV mode.

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
question:

1. Is an invalid UTF-8 byte a warning, like the BOM, or still a refusal?
   (`encoding/invalid-utf8-refused`)
2. Does a lone CR break a record? (`encoding/lone-cr-line-breaks-warn`)
3. Is a header with no data rows a table? (`table/header-only-accepted`)
4. Is a quote left open at the end of the file refused?
   (`rfc4180/unterminated-quote-refused`)
5. Is a blank line between rows a record? (`fieldcount/blank-line-between-rows-refused`)
6. Is a `#` line a comment or a record? (`fieldcount/hash-line-is-a-record-refused`)
7. Is NFC the whole of column-name comparison, with case significant?
   (`columns/case-differing-columns-accepted`)
8. How does a sidecar fail when its JSON is invalid?
   (`identity/sidecar-invalid-json-refused`)
9. How does it fail when it repeats a member?
   (`identity/sidecar-duplicate-key-member-refused`)
10. How does it fail when it names a column the file lacks?
    (`identity/sidecar-key-names-absent-column-refused`)
11. Do §9.18 and §9.19 apply to a CSV? (`nonapply/pipe-and-hash-values-accepted`)
12. Is whitespace around a field part of its value? No case was written.

SPEC.md §13 has since settled 4 and 5, in the direction the cases took. The
rest stand as the cases read them.
