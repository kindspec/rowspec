<!-- SPDX-License-Identifier: CC0-1.0 -->
# The fixture tree

CC0. Copy it into any implementation, in any language. Everything a runner
needs is in the files; nothing is in Python.

## Shape

    cases/<kind>/<case-name>/
        expect.json          what to assert  (required; its presence IS the case)
        input.mdtbl          the artifact under test
        <other>.mdtbl        companion artifacts, if the case needs them
        WHY.md               prose, ignored by the runner

A directory is a case **iff** it contains `expect.json`. A directory without
one is walked past — that is what makes companion subdirectories possible, and
`conformance/reserved/_outside/`, if those cases are ever run.

`kind` in `expect.json` is authoritative; the parent directory name is a filing
convention, not an input.

## The case directory is a repository

**Nothing in this tree uses these rules yet.** The format's cross-artifact
reference, `lookup()`, is reserved and not defined in this edition (SPEC §7),
and its cases are kept, unrun, in `conformance/reserved/`. The rules below are
how those cases are laid out, and how a later edition that specifies `lookup()`
would lay out its own.

Two rules, and everything about cross-artifact behaviour follows from them:

1. **The case directory is the artifact's directory.** `input.mdtbl` sits in
   it, and the reserved design resolves a `lookup()` path *relative to the
   referring artifact* — so a companion is just a file next to `input.mdtbl`,
   addressed by its ordinary relative path. `lookup(customers.mdtbl, ...)` finds
   `<case>/customers.mdtbl`. `lookup(sub/b.mdtbl, ...)` finds
   `<case>/sub/b.mdtbl`, and a lookup *inside* `sub/b.mdtbl` written as
   `lookup(c.mdtbl, ...)` finds `<case>/sub/c.mdtbl`, because it is resolved
   relative to **b**, not to the case root.

2. **The case directory is also the repository root.** The reserved design
   confines a lookup target *to the repository*; a case is a self-contained
   one-artifact repository, so a path that resolves above the case directory
   has escaped and must be refused. `reserved/parse/lookup-path-escape` is that test, and
   `reserved/_outside/` exists solely to give it a real file to reach for — so
   that an implementation which does not enforce confinement fails loudly with
   a value rather than quietly with a missing file.

There is no manifest, no `files` list, and no new `expect.json` field. A
second artifact is expressed the only way a repository expresses one: by
being a file at a path.

A runner in another language therefore needs to do exactly one extra thing:
**tell the implementation which directory the artifact lives in.** In Python
that is `evaluate(text, base=case_dir)`.

`input.mdtbl` is the primary artifact for every kind except `merge` and
`confluence`, which take `base.mdtbl` / `ours.mdtbl` / `theirs.mdtbl` /
`branch<N>.mdtbl` instead and stage them through real git.

A `parse` case may hold its artifact as `input.bin` instead, and must when
the bytes are not UTF-8: a runner reads every `.mdtbl` in the tree as UTF-8
text, so one that does not decode stops the whole tree rather than failing
one case. The runner reads `input.bin` itself, as bytes, and hands them to
the implementation's bytes entry point, which decides SPEC §9.14 before
anything else; in Python that is `evaluate_bytes(data)`. A case holding both
`input.mdtbl` and `input.bin` fails, because which one it checks would be a
guess.

## Kinds

| kind | fields | assertion |
| --- | --- | --- |
| `parse` | `accept`, `refusal` | the artifact is accepted, or refused with that SPEC §9 identifier |
| `roundtrip` | — | `render(structure(bytes)) == bytes` |
| `eval` | `aggregates` | each named table-level aggregate has that value |
| `rowrel` | `row_index`, `column`, `value` | that one cell of that one row, in the *derived* order |
| `mutate` | `row_key`, `column`, `value`, and `expect`/`aggregate`+`result` | a write through the structure is refused, or is visible, or changes an aggregate |
| `canon` | `check` | `idempotent` / `preserves-values` / `removes-padding` / `already-canonical` |
| `merge` | `git_outcome`, `then`, `aggregates` | what stock git does, and what the reader then says |
| `confluence` | `branches` | every merge order yields one outcome |

`rowrel` is named for the operators that motivated it, but it is the general
single-cell assertion and is what the reserved `lookup()` cases use.

`refusal` is the identifier that opens the refusal's entry in SPEC §9, such as
`"duplicate-row-id"`. Where a file violates several refusals and §9 leaves
which one is reported to the implementation, `refusal` is a list of every
identifier that applies, and reporting any one of them passes. A refusing
`parse` case with no `refusal` fails rather than accepting a refusal for any
reason. The message is never asserted on: implementations word it freely, and
asserting invented wording would test one implementation's phrasing rather
than the format. A Python implementation reports the identifier as the
`refusal` attribute of the exception it raises; a runner in another language
reads it from wherever that language's binding puts it.

`case-body.schema.json` in this directory lists §9's identifiers, so kindkit's
case-tree validator refuses a `refusal` that is misspelt or names no §9 entry.

Values in `expect.json` are JSON: a number is a number, an error is the string
`"#REF!(...)"`, a blank cell is `""`.

## Ground rules

- **Fixtures are exact bytes.** `.gitattributes` disables end-of-line
  normalisation for this tree. Never reformat a fixture.
- **A case may fail.** The suite is written from `SPEC.md` and runs ahead of
  any implementation; a failing case is a finding, not a bug in the case. Add,
  do not edit: changing an existing case to match an implementation is how a
  suite stops measuring anything.

## Provenance of the `refusal` identifiers

The identifiers in this tree's `refusal` fields (#61) were not chosen by the
author of `reference/rowspec/`. Two exports were copied from a working tree
based on commit `ce24fa9`, which was then the head of `main`. Besides the
original files, that working tree held a draft of SPEC.md §9 that gave each
entry its identifier, and the new version of this README; the export for
`rowspec_alt` also held the new `conformance/run_cases.py`. Neither export
held a `.git` directory.

The case tags and `rowspec_alt`'s identifiers were assigned by two separate
authors, each confined to their own export.

- **The cases** were tagged in an export holding only the draft `SPEC.md` and
  `conformance/cases/`: no implementation, no runner and no mutation gate.
  Each refusing `parse` case's `refusal` was assigned from the draft, the
  fixture bytes and the case's `WHY.md`.
- **`reference/rowspec_alt/`** was tagged in an export holding the draft
  `SPEC.md`, `conformance/cases/` without identifiers,
  `conformance/run_cases.py`, `reference/rowspec_alt/` and build caches, but
  not `reference/rowspec/`.

`SPEC.md`, and the alt export's runner, were refreshed once during the
tagging, when entry 25 (`order-without-key`) was added to the draft.

The two export directories still exist outside this repository. Every file
in them that the tagging did not edit is byte for byte the file at
`ce24fa9`, and the draft `SPEC.md` they hold is in no commit. The exact
commands that made the exports are not recorded in this repository.

Since then, two identifier assignments have changed with SPEC.md rather than
with an implementation. `parse/bom-refused` became `leading-bom` when §9.14
was split. `parse/order-unrecognised-construct-refused` gained
`rowrel-without-order`: its file also uses `cumulative()`, so with no valid
`order` declared, §9.9 applies too.

## Cases written without the implementation

Later batches were written by authors who were not the author of
`reference/rowspec/` or `reference/rowspec_alt/` and did not read either.
Each author derived every expected outcome from SPEC.md, read the existing
case tree for its format, and recorded the passage the outcome rests on in
the case's `WHY.md`.

- **The first batch** (#92, #100, #102) was written on a branch from
  `d51f27a`. In this tree it covers an order column blank in every row,
  a header group aggregate over a missing column, and `sum` and `avg` over a
  stored cell beyond binary64. Its CSV-profile cases are in `cases-csv/`.
  The exact export it was written from is not recorded here.
- **The second batch** (#100, #107) was written in a directory holding no
  `.git` and no implementation, made with

      git archive 2975479 SPEC.md README.md CONTRIBUTING.md AGENTS.md conformance/cases conformance/cases-csv

  plus SPEC.md from `3626006`, the branch that adds §4.1.11's rule that
  `key :=` names a stored column. Issue and pull request descriptions were
  read for which behaviours to pin and which questions are open, never for
  an expected value. It covers that rule
  (`parse/key-names-*`), a stored cell beyond binary64 as an operand of row
  arithmetic, `if`, `prior`, `delta` and `cumulative`, `min` and `max` over
  such a cell, and a header `where` predicate that names a missing column
  before a computed column or before a numeric right-hand side.
  It writes no case for a question SPEC.md leaves open: which error an
  aggregate or `delta` carries when its operands hold two different
  errors, and what a numeric literal beyond binary64 is.
- **The third batch**, by the second batch's author, was written against
  SPEC.md at `080d0ae` in a checkout of that commit, opening only SPEC.md,
  this tree, and the case-count floor in `conformance/run_cases.py`. It
  covers the leftmost of two missing names inside one `where` predicate, as
  a header cell and as a declaration (`*-leftmost-missing-name-wins*`); a
  group aggregate on a cycle whose predicate names a computed column or has
  a numeric right-hand side, which is still refused
  (`*cyclic-group-aggregate-*`); an unknown function, and a computed column
  in a predicate, on a declaration whose aggregated column is missing
  (`declaration-unknown-function-*`, `declaration-predicate-*-after-a-*`);
  and `cumulative` across a positive then a negative infinite cell.
  It writes no case for `cumulative` from an infinite cell into a blank,
  which SPEC.md does not settle.
- **The fourth batch**, by the same author, was written against SPEC.md at
  `32466e0`, which holds the rulings on #110, #115, #116, #117 and #118,
  opening only SPEC.md, the two case trees, and the case-count floors in
  `conformance/run_cases.py`. It covers `key :=` in function form
  (`parse/key-in-*`); the ranking of several `#REF!` values in one
  aggregate, with each order-independence claim made by a row-swapped twin
  (`eval/aggregate-ranks-*`); `delta` when both rows give an error, and over
  a computed `#REF!(/0)`; an overlong literal, header errors against row
  errors, and `1 / 0` in an `if` branch (`rowrel/overlong-literal-*`,
  `rowrel/*header-error*`, `rowrel/division-by-zero-*`); a blank key value;
  `prior` over a stored text cell and over a cell of U+00A0; an order column
  holding a U+00A0 cell; and a stored cell spelled like an error. Its
  CSV-profile cases are in `cases-csv/columns/`.
- **The fifth batch**, by the same author, was written against SPEC.md at
  `40e5647`, opening only SPEC.md, this tree, and the case-count floor in
  `conformance/run_cases.py`. It covers evaluation by dependency where a
  computed column's name sorts before the column it reads, each with the
  header in both orders (`rowrel/*-later-sorting-*`); a column that names
  itself through `prior`, `delta`, `cumulative` or a group aggregate, and a
  column depending on one (`*-of-itself-*`, `*-self-cycle-*`,
  `group-aggregate-over-itself-*`); an unknown function in a header group
  call (`parse/*-function-in-a-header-group-call-*`); row-relative operators
  over computed values that hosts print in exponent form
  (`rowrel/*-tiny-computed-*`, `rowrel/*-large-computed-*`); and
  `cumulative` over a computed `#REF!(/0)`. A review pass on the same
  terms added a per-row group aggregate over a `prior` column
  (`rowrel/group-aggregate-over-a-prior-column-*`), `prior`, `delta` and
  `cumulative` over a missing column in the first row
  (`rowrel/*-of-a-missing-column-*`), and first-row assertions for the
  cycles above.
- **The sixth batch**, by the same author, was written against SPEC.md at
  `72abdc4`, opening only SPEC.md, this tree, and the case-count floor in
  `conformance/run_cases.py`. It puts `#REF!(/0)` against `#REF!(empty)` in
  one aggregate, with a row-swapped twin
  (`eval/aggregate-ranks-div-zero-over-empty*`).
- **The seventh batch**, by the same author, was written against SPEC.md at
  `7514d04`, opening only SPEC.md, this tree, and the case-count floor in
  `conformance/run_cases.py`. It pins that an unknown function in a group
  aggregate over its own column is refused although the column is on a
  cycle, with a known-function control
  (`parse/*-function-in-a-group-aggregate-over-itself-*`).
- **The eighth batch** was written by an author who was not the author of
  either implementation and did not read either, against SPEC.md at
  `29edd7c` in a worktree of that commit, opening only SPEC.md, AGENTS.md,
  CONTRIBUTING.md, the two case trees, the case-count floors in
  `conformance/run_cases.py`, and the lines of README.md, ROADMAP.md and
  CHANGELOG.md that state those counts. Its cases are these, named exactly:
  - `delta(c)` in the first row: `rowrel/delta-first-row-on-a-blank-cell-is-ref`,
    `rowrel/delta-first-row-on-a-text-cell-is-ref`,
    `rowrel/delta-first-row-over-a-computed-div-zero-carries-it`,
    `rowrel/delta-first-row-over-a-computed-number-is-blank` and
    `rowrel/delta-first-row-over-an-unresolved-name-carries-it`.
  - Trimming to ASCII space and tab: `eval/tab-padding-around-a-number-is-trimmed`,
    `eval/em-space-padding-is-not-trimmed`,
    `eval/ideographic-space-padding-is-not-trimmed`,
    `eval/tab-padded-column-name-resolves`,
    `parse/key-values-differing-by-tab-padding-are-duplicates-refused`,
    `parse/key-value-with-a-trailing-no-break-space-refused`,
    `parse/key-value-with-a-leading-em-space-refused`,
    `parse/key-value-with-a-trailing-ideographic-space-refused`,
    `parse/order-column-tab-padded-number-accepted`,
    `parse/order-column-no-break-space-padded-number-mixes-types-refused`,
    `parse/order-column-em-space-padded-number-mixes-types-refused`,
    `parse/order-column-ideographic-space-padded-number-mixes-types-refused`,
    `parse/column-name-with-a-trailing-no-break-space-refused`,
    `parse/column-name-with-a-leading-em-space-refused` and
    `parse/computed-column-name-with-an-ideographic-space-refused`.
  - Line endings, for each of `line-separator`, `next-line`, `form-feed`
    and `vertical-tab`: `eval/<char>-inside-a-cell-does-not-end-the-line`,
    `eval/<char>-padding-is-not-trimmed` and
    `eval/annotation-holding-a-<char>-stays-inert`; and
    `parse/form-feed-after-the-closing-pipe-refused`,
    `parse/vertical-tab-after-a-declaration-refused`,
    `eval/tab-after-a-declaration-is-whitespace`,
    `parse/lone-cr-ending-the-last-line-refused` and
    `parse/lone-cr-inside-an-annotation-refused`.
  - Order values §4.1.6 or §4.1.7 refuse:
    `parse/order-column-leading-plus-mixes-types-refused`,
    `parse/order-column-bare-leading-point-mixes-types-refused`,
    `parse/order-column-bare-trailing-point-mixes-types-refused`,
    `parse/order-column-non-ascii-digit-mixes-types-refused`,
    `parse/order-date-non-ascii-digits-mixes-types-refused` and
    `rowrel/order-column-of-number-like-text-sorts-by-code-point`.
  - A declaration's argument:
    `parse/declaration-argument-with-a-leading-nul-refused`,
    `parse/declaration-argument-with-a-trailing-soh-refused`,
    `parse/declaration-argument-with-a-leading-zero-width-space-refused`,
    `parse/declaration-argument-with-a-trailing-zero-width-space-refused`
    and `eval/declaration-argument-padded-with-space-and-tab`.
  - Whitespace before a call's `(`:
    `parse/prior-with-a-space-before-its-paren-refused`,
    `parse/delta-with-a-tab-before-its-paren-refused`,
    `parse/cumulative-with-a-space-before-its-paren-refused`,
    `parse/declaration-sum-with-a-space-before-its-paren-refused` and
    `parse/declaration-count-with-a-tab-before-its-paren-refused`.
  - Empty or whitespace-only column names:
    `parse/empty-stored-column-name-refused`,
    `parse/whitespace-only-stored-column-name-refused`,
    `parse/empty-computed-column-name-refused`,
    `parse/whitespace-only-computed-column-name-refused`,
    `parse/two-empty-stored-column-names-refused` and
    `parse/two-empty-computed-column-names-refused`.
  - A `#` in a header string literal:
    `eval/hash-inside-a-string-literal-in-a-header-if` and
    `eval/hash-inside-a-string-literal-in-a-header-where`.

  Its CSV-profile cases are listed in `cases-csv/README.md`. It writes no
  case for number or date recognition in the CSV profile, which §13 does
  not define.
- **The ninth batch** was written by an author who was not the author of
  either implementation and did not read either, against SPEC.md at
  `7652865` in a worktree of that commit, opening only SPEC.md, AGENTS.md,
  CONTRIBUTING.md, the two case trees, the case-count floors in
  `conformance/run_cases.py`, and the lines of README.md, ROADMAP.md and
  CHANGELOG.md that state those counts. Its cases are these, named exactly:
  - A declaration with an empty argument:
    `parse/declaration-order-by-with-an-empty-argument-refused`,
    `parse/declaration-sum-with-an-empty-argument-refused` and
    `parse/declaration-count-with-an-empty-argument-refused`.
  - A declaration argument holding `-` or `.`:
    `parse/declaration-sum-argument-with-a-hyphen-refused`,
    `parse/declaration-sum-argument-with-a-dot-refused`,
    `parse/declaration-sum-argument-with-a-hyphen-before-where-refused` and
    `parse/declaration-order-argument-with-a-hyphen-refused`; with the
    controls `eval/declaration-arguments-that-are-idents-control` and
    `parse/declaration-order-argument-that-is-an-ident-accepted`.
  - Non-finite spellings in an order column:
    `parse/order-column-of-only-non-finite-spellings-refused`,
    `parse/order-column-of-one-non-finite-spelling-in-mixed-case-refused`,
    `parse/order-text-column-with-one-inf-cell-refused`,
    `parse/order-text-column-with-one-nan-cell-refused` and
    `parse/order-text-column-with-one-infinity-cell-refused`; with the
    control `parse/order-text-column-with-non-finite-lookalikes-accepted`.
  - A row-relative name inside a header string literal, with no order:
    `eval/prior-inside-a-string-in-a-header-where-is-not-a-call`,
    `eval/prior-inside-a-string-in-a-header-if-is-not-a-call`,
    `eval/delta-inside-a-string-in-a-header-where-is-not-a-call`,
    `eval/delta-inside-a-string-in-a-header-if-is-not-a-call`,
    `eval/cumulative-inside-a-string-in-a-header-where-is-not-a-call` and
    `eval/cumulative-inside-a-string-in-a-header-if-is-not-a-call`; with the
    control `parse/prior-call-beside-a-string-mention-without-order-refused`.

  Its CSV-profile cases are listed in `cases-csv/README.md`. It writes no
  case for a signed non-finite spelling such as `-inf` in an order column,
  which SPEC.md does not settle.
- **The tenth batch** was written by an author who was not the author of
  either implementation and did not read either, against SPEC.md at
  `e2b121a` in a worktree of that commit, opening only SPEC.md, AGENTS.md,
  CONTRIBUTING.md, the two case trees, the case-count floors in
  `conformance/run_cases.py`, the `justfile`, the test names in
  `tests/test_conformance.py`, and the lines of README.md, ROADMAP.md and
  CHANGELOG.md that state those counts. Its cases are these, named exactly:
  - A row-relative name, then a space or tab, then `(`, with no order
    declared, refused as `malformed-formula` alone:
    `parse/prior-with-a-space-before-its-paren-without-order-refused`,
    `parse/delta-with-a-tab-before-its-paren-without-order-refused` and
    `parse/cumulative-with-a-space-before-its-paren-without-order-refused`.
  - A signed non-finite spelling in an order column, alone and beside text:
    `parse/order-column-of-only-minus-inf-refused`,
    `parse/order-text-column-with-one-minus-inf-cell-refused`,
    `parse/order-column-of-only-plus-nan-refused`,
    `parse/order-text-column-with-one-plus-nan-cell-refused`,
    `parse/order-column-of-only-minus-infinity-mixed-case-refused`,
    `parse/order-text-column-with-one-minus-infinity-mixed-case-cell-refused`,
    `parse/order-column-of-only-plus-inf-upper-case-refused` and
    `parse/order-text-column-with-one-plus-inf-upper-case-cell-refused`.
  - Their controls, accepted:
    `parse/order-text-column-with-a-double-minus-inf-cell-accepted`,
    `parse/order-text-column-with-a-plus-minus-nan-cell-accepted`,
    `parse/order-text-column-with-a-minus-info-cell-accepted` and
    `parse/order-text-column-with-a-minus-space-inf-cell-accepted`.

  It also brings the quotations of §6 and §9.10 in the `WHY.md` files of
  `parse/order-column-of-one-non-finite-spelling-in-mixed-case-refused`,
  `parse/order-column-of-only-non-finite-spellings-refused`,
  `parse/order-text-column-with-non-finite-lookalikes-accepted` and
  `parse/order-text-column-with-one-{inf,infinity,nan}-cell-refused` up to
  the text that settled the signed spelling, without changing any expected
  outcome. Its CSV-profile cases are listed in `cases-csv/README.md`.
- **The eleventh batch** (#202) was written by an author who was not the
  author of either implementation and did not read either, against SPEC.md
  at `81df2ad` in a worktree of that commit, opening only SPEC.md,
  AGENTS.md, CONTRIBUTING.md, this tree, `conformance/run_cases.py`, the
  text of #202, the lines of README.md and ROADMAP.md that state the case
  count, and CHANGELOG.md. #202 lists the identifier it expects for each
  of these inputs. Each outcome here was derived from SPEC.md and then
  checked against that list; where SPEC.md admits more identifiers than
  #202 names, the case lists them all and its `WHY.md` says why. The
  widening of `parse/order-by-with-a-where-refused` to three identifiers
  was made after its author had read the `order` branch of the `where`
  guard in `reference/rowspec/table.py`, to disable it for a mutation
  check; that branch reports `malformed-declaration`, which the case named
  before and after. Its cases are these, named exactly:
  - An `order` declaration that is not `by(c)`:
    `parse/order-in-count-form-with-where-refused` and
    `parse/order-by-with-a-where-refused`.
  - `order := by(c)` where `c` is no column, or an aggregate, with and
    without rows:
    `parse/order-by-a-missing-column-with-no-rows-refused`,
    `parse/order-by-a-missing-column-with-rows-refused`,
    `parse/order-by-an-aggregate-name-with-no-rows-refused` and
    `parse/order-by-an-aggregate-name-with-rows-refused`.
  - Two refusals that both apply, either of which passes:
    `parse/order-by-a-missing-column-without-key-refused`,
    `parse/order-by-a-missing-column-without-key-with-no-rows-refused` and
    `parse/order-by-then-order-in-count-form-refused`.
- **The twelfth batch** (#99) was written by an author who was not the
  author of either implementation and did not read either, against SPEC.md
  at `81df2ad` in a worktree of that commit, opening only SPEC.md,
  AGENTS.md, CONTRIBUTING.md, this tree, `conformance/run_cases.py` and
  issue #99. Each case is a file to which exactly one §9 entry applies, and
  asserts that identifier alone:
  - `parse/conflict-marker-after-the-declarations-refused` (`conflict-marker`);
  - `parse/alignment-style-data-row-without-a-key-refused`
    (`alignment-row-in-data`).

  It writes no such case for `lone-cr`, `malformed-table-line`,
  `ident-compared-in-if` or `alignment-field-count`, because SPEC.md leaves
  none possible. A lone `CR` is not a `char`, so its line matches no
  alternative of `line` and §9.19, §9.18 or §9.12 applies with §9.15.
  §9.18 says of its own lines that they meet §9.19 too. §9.24 says its
  comparison "*is* reachable by the grammar", so the header cell holding it
  is also §9.20. And §4 puts the alignment row's field count among what makes
  it valid, so a count mismatch is also §9.21, as `parse/align-mismatch`
  already says.
- **`parse/non-utf8-byte-in-a-cell-refused`** (#222) asserts
  `bad-encoding` alone, and is the first case held as `input.bin`. It was
  written from SPEC.md at rowspec `1786215` alone, by an author who saw no
  implementation. Its `WHY.md` lists the files read, by sha256.
