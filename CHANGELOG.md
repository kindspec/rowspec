# Changelog

Notable changes to rowspec. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning is [SemVer](https://semver.org/), with the caveat in `SPEC.md`'s
preamble: conformance is a claim about a **version of the suite**, not about the
prose, and where the two disagree the suite wins.

## [Unreleased]

`v0.1.0` tags `625ddb2`. Everything below has landed on `main` since;
documentation-only commits are not listed separately. A hand-maintained count
of them used to stand here and was wrong within two commits, which is the
argument against writing one.

### Added

- **A GitHub Action** (`c19538a`) running both `check` and `eval`, with a
  self-test that asserts in both directions: that it fails a well-formed table
  whose total is `#REF!`, and that the same file passes with `eval: false` — so
  the first assertion is about `eval` and not about the file.

- **The xlsx boundary** — export ships as the optional `rowspec[xlsx]` extra
  from `export/rowspec_xlsx`, outside `reference/`, which stays
  standard-library-only. `tests/test_boundary.py` fails if anything under
  `reference/` imports outside the standard library, so the rule is enforced
  rather than remembered. The exporter itself is deliberately minimal: literal
  values only — a stored cell is written as text even when it begins with `=`,
  and the key column is never coerced to a number, because §9.16 makes a key an
  identifier and `007` and `7` are two rows. Closes #34; #35 and #36 are the
  round-trip claim.

### Changed

- **The runner and the mutation gate are now
  [kindkit](https://github.com/kindspec/kindkit)** (closes #33). rowspec is the
  kit's first consumer, and the adoption is measured rather than asserted: 0
  failures across 410 cases on both implementations, and 74 killed, 0 survived,
  2 equivalent, 0 stale, with the same verdict and the same killing cases for
  all 76 mutants before and after. What is left in `conformance/run_cases.py`
  is the eight handlers that know what a rowspec case *means*; what is left in
  `conformance/mutants.py` is the mutant table and the probe that runs this
  suite. Walking the tree, reading fixtures as exact bytes, splicing mutants as
  normalised token runs, hashing, and the accounting are the kit's, and are the
  same for every kind.

  **The sdist ships the suite but cannot declare kindkit.** PEP 735
  dependency-groups are not packaged metadata, and a direct git requirement
  cannot go in `optional-dependencies` because PyPI rejects it, so an unpacked
  sdist needs `uv sync --group dev` (network, and git) before `just conform`
  will run. Measured: `python3 conformance/run_cases.py` inside an unpacked
  sdist raises `ModuleNotFoundError: No module named 'kindkit'`. Tracked in
  #47; publishing kindkit to PyPI is the real fix.

  kindkit is a **dev** dependency, pinned to a commit rather than a branch.
  `dependencies` stays empty, `pip install rowspec` still pulls nothing, and
  `reference/` still imports the standard library and nothing else —
  `tests/test_boundary.py` is unchanged and still holds that line.

- **The runner has three exit codes, not two**: 0 every case passed, 1 at least
  one case failed, 2 the fixture tree yielded no verdict at all. A missing
  root, an empty root, and a root that has shrunk below the 410 cases `find
  conformance/cases -name expect.json | wc -l` reports are all the third thing.
  "Every case passed" and "no case ran" no longer look alike from the outside.

### Fixed

- **An `EQUIVALENT` claim naming a mutant that no longer exists is a hard
  failure** (closes #37). The claim is a field on the mutant now, not a row in
  a side table keyed by name, so it cannot outlive what it excuses. The
  orphaned `float-accepts-thousands-separators` entry — ignored in silence
  since the mutant it named was replaced — is removed. Watched red: putting it
  back exits 2 with `HARD FAILURE: equivalence claimed for a mutant that does
  not exist`.
- **A mutant that leaves the suite with no verdict is reported BROKEN, never
  killed** (closes #45). The `<runner crashed>` sentinel is gone. The probe
  reports what the run *produced* — the exit code, the accounting line, the
  case count it accounts for, and whether that count agrees with the `FAIL`
  lines above it — so a run that opened no case cannot be read as one that
  caught something. Watched red: a mutant that makes `table.py` unimportable
  scored `killed (1 case(s): <runner crashed>)` at exit 0 before, and `BROKEN`
  at exit 1 after.
- **A stale `.pyc` can no longer credit a mutant with its neighbour's verdict**
  (closes #44). The kit purges the scratch module's cached bytecode after every
  write, so two mutations of the same size inside one mtime second are no
  longer indistinguishable to the loader.

  The ingredients are in the table today. Applying all 76 mutants and measuring
  `len(out.encode())` gives **14 groups of mutants that produce byte-identical
  file sizes**, the largest holding five. `strip-eats-non-ascii-spaces` and
  `allow-duplicate-order-declaration` are one such pair — both 49,765 bytes
  against an unmutated 49,770 (`wc -c reference/rowspec/table.py`) — and they
  are killed by disjoint cases.

  Watched red on exactly those two, unmodified, through a deliberately fast
  probe over the same adapter and two real fixtures, because a 2-second
  410-case run puts consecutive writes ~2s apart and never reaches the window:

      BEFORE  killed  strip-eats-non-ascii-spaces        (eval/non-ascii-space-padding-refused)
              killed  allow-duplicate-order-declaration  (eval/non-ascii-space-padding-refused)
      AFTER   killed  strip-eats-non-ascii-spaces        (eval/non-ascii-space-padding-refused)
              killed  allow-duplicate-order-declaration  (parse/dup-order-decl)

  Before, the second mutant is credited with the *first* one's killing case —
  a case that cannot detect it. Both runs exit 0, which is the point: the loud
  symptom of this defect is a false survivor, and the quiet one is a false
  kill.

- **The vacuous-implementation test could be satisfied by measuring nothing.**
  `tests/test_conformance.py` asserted `returncode != 0`, which meant "cases
  failed" while the runner had two exit codes and means "cases failed OR the
  tree yielded no verdict" now that it has three. Watched: the vacuous
  implementation over an empty root exits 2 and the old assertion passed. It
  asserts `== 1`.
- **The mutation probe had no subprocess timeout**, so a mutant that made the
  suite loop rather than crash hung the gate until CI's job timeout, with no
  verdict and nothing saying so. It now times out and reports the no-verdict it
  already has a name for. Watched: the same run takes exit 124 from an outer
  `timeout 15` without it, and refuses in 3s with it.

- **`just test` had never run in CI.** The conformance suite and the mutation
  gate did, through `just conform` and `just mutants`, so the gap was invisible
  — but `tests/` also holds the CSV refusals and the CLI's own behaviour, and
  nothing on a forge ran them. It now runs with the xlsx extra deliberately
  absent, behind a step that asserts the extra really is absent.
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
