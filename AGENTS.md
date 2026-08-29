# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project

rowspec is a specification, an executable conformance suite, and a reference
implementation for `.mdtbl` — tabular data designed so that stock git merges it
correctly or refuses, never silently wrong. The suite is the deliverable; the
implementation exists so the suite has something to check.

## Stack

- **Python 3.11+**, managed with `uv`. Standard library only in `reference/`.
- **ruff** for format and lint, **pytest** for tests, **just** as task runner.
- A real `git` binary is a hard dependency of the conformance suite.

## Layout

```
SPEC.md               the normative specification (CC-BY-4.0)
conformance/cases/    fixtures: directories of real files + expect.json (CC0)
conformance/          the tree-driven runner and the mutation gate (MIT)
reference/rowspec/    the reference implementation (Apache-2.0 OR MIT)
tests/                pytest wrappers around the suite
```

## Commands

```sh
just setup    just check    just test    just conform    just mutants
```

## Conventions

- **`reference/` is standard library only.** A dependency there is a dependency
  every independent implementation inherits.
- Fixtures are exact bytes. `conformance/cases/` is excluded from whitespace
  hooks for that reason — never "tidy" a fixture.
- Errors name entities, never offsets. `#REF!(unit)`, not "error at line 7".
- New behaviour needs a fixture, and the fixture should be able to fail.

## Constraints

- **Do not add a case in the same change that adds the code it covers.** See
  CONTRIBUTING.md — this is the project's one hard process rule and it exists
  because it was violated three times during design.
- Do not make correctness depend on a git merge driver, a clean/smudge filter,
  or a hook. None of them travel; see SPEC.md §11.
- Do not add a coordinate to the grammar. Not a cell reference, not a row
  offset, not a column index. Every silent-wrong merge found during design
  traced back to one.
- Do not commit derived values.
