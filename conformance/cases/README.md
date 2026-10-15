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

Five later batches were written by authors who were not the author of
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
