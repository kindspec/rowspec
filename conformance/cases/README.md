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
one is walked past — that is what makes companion subdirectories and
`_outside/` possible.

`kind` in `expect.json` is authoritative; the parent directory name is a filing
convention, not an input.

## The case directory is a repository

Two rules, and everything about cross-artifact behaviour follows from them:

1. **The case directory is the artifact's directory.** `input.mdtbl` sits in
   it, and SPEC §7 resolves a `lookup()` path *relative to the referring
   artifact* — so a companion is just a file next to `input.mdtbl`, addressed
   by its ordinary relative path. `lookup(customers.mdtbl, ...)` finds
   `<case>/customers.mdtbl`. `lookup(sub/b.mdtbl, ...)` finds
   `<case>/sub/b.mdtbl`, and a lookup *inside* `sub/b.mdtbl` written as
   `lookup(c.mdtbl, ...)` finds `<case>/sub/c.mdtbl`, because it is resolved
   relative to **b**, not to the case root.

2. **The case directory is also the repository root.** SPEC §7 confines a
   lookup target *to the repository*; a case is a self-contained one-artifact
   repository, so a path that resolves above the case directory has escaped and
   must be refused. `parse/lookup-path-escape` is that test, and
   `cases/_outside/` exists solely to give it a real file to reach for — so
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
| `parse` | `accept`, `refusal_contains` | the artifact is accepted, or refused with a message containing that substring |
| `roundtrip` | — | `render(structure(bytes)) == bytes` |
| `eval` | `aggregates` | each named table-level aggregate has that value |
| `rowrel` | `row_index`, `column`, `value` | that one cell of that one row, in the *derived* order |
| `mutate` | `row_key`, `column`, `value`, and `expect`/`aggregate`+`result` | a write through the structure is refused, or is visible, or changes an aggregate |
| `canon` | `check` | `idempotent` / `preserves-values` / `removes-padding` / `already-canonical` |
| `merge` | `git_outcome`, `then`, `aggregates` | what stock git does, and what the reader then says |
| `confluence` | `branches` | every merge order yields one outcome |

`rowrel` is named for the operators that motivated it, but it is the general
single-cell assertion and is what the `lookup()` cases use.

`refusal_contains: ""` means *refuse, for any stated reason*. It is used where
the spec mandates a refusal but names no message — asserting invented wording
would test the reference implementation's phrasing rather than the format.

Values in `expect.json` are JSON: a number is a number, an error is the string
`"#REF!(...)"`, a blank cell is `""`.

## Ground rules

- **Fixtures are exact bytes.** `.gitattributes` disables end-of-line
  normalisation for this tree. Never reformat a fixture.
- **A case may fail.** The suite is written from `SPEC.md` and runs ahead of
  any implementation; a failing case is a finding, not a bug in the case. Add,
  do not edit: changing an existing case to match an implementation is how a
  suite stops measuring anything.
