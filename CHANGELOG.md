# Changelog

Notable changes to rowspec. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning is [SemVer](https://semver.org/), with the caveat in `SPEC.md`'s
preamble: conformance is a claim about a **version of the suite**, not about the
prose, and where the two disagree the suite wins.

## [Unreleased]

`v0.1.0` tags `625ddb2`; three commits have landed on `main` since.

### Added

- **A GitHub Action** (`c19538a`) running both `check` and `eval`, with a
  self-test that asserts in both directions: that it fails a well-formed table
  whose total is `#REF!`, and that the same file passes with `eval: false` — so
  the first assertion is about `eval` and not about the file.

### Fixed

- The mutation gate took its paths from the working directory, so it reported
  differently depending on where it was invoked from (`c0b9a7a`, closes #31).
  Paths are now anchored to `__file__`.

See [ROADMAP.md](ROADMAP.md) for what 0.2.0 is scoped to.

## [0.1.0] — 2026-08-31

Draft 0. First release.

### Added

- **`SPEC.md`** — the normative specification, including §4.1's lexical grammar
  and §4.2's expression grammar, both written after an independent
  implementation's report showed the prose was insufficient without them.
- **The conformance suite** — 410 cases as directories of real files plus one
  `expect.json`, driven by a runner that never imports the case definitions.
  The 19 `merge/` cases are the ones with no prior art: they check out two
  branches, run stock `git merge`, evaluate the merged file, and assert on the
  computed number. The rest cover parsing (144), evaluation (135), row-relative
  operators (70), canonicalisation (21), round-trip (11), mutation (7) and
  confluence (3).
- **The mutation gate** — 76 mutants; a surviving mutant is a failure and so is
  a stale one whose pattern no longer matches the source.
- **A second implementation** — `reference/rowspec_alt/`, written from `SPEC.md`
  alone by an author forbidden to read `reference/rowspec/`, running against the
  same fixture tree in CI.
- **CSV mode** — 4 of the 13 refusals apply to a bare `.csv` with no migration,
  8 with a five-line sidecar naming the key and the order column; 5 are
  `.mdtbl`-only by construction. See `docs/csv.md`.
- **Publication to PyPI** and the per-directory licence split.

### Fixed during the build, and worth recording

Four of these are the pattern this project kept reproducing — **a check that
could not fail, reporting a pass**. `docs/rationale.md` enumerates the full set.

- The conformance runner took its fixture root as a relative path, so from the
  repository root it walked nothing and printed `0 failure(s)` over 226 unopened
  cases, four of them failing. An empty tree is now a hard failure.
- The mutation gate disarmed itself on a `ruff format` and reported a pass; 23
  of its patterns had gone stale. Staleness is now a failure.
- `canon = lambda x: x` scored 129/131 — a fixture with no runner branch.
- A per-vendor subtotal over a computed column evaluated to `0` in every row
  with `check` reporting `0 refused` and `eval` exiting `0`.

The fifth is a different shape and belongs beside them: `_ast()` called
`ast.parse`, so §4.2 was normative prose while Python's grammar was what
actually ran. The two grammars diverged invisibly until differential evaluation
against 55,681 real spreadsheet cells found it — not a check that could not
fail, but a check that was never against the specification at all.

[Unreleased]: https://github.com/kindspec/rowspec/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kindspec/rowspec/releases/tag/v0.1.0
