# Changelog

Notable changes to rowspec. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning is [SemVer](https://semver.org/), with the caveat in `SPEC.md`'s
preamble: conformance is a claim about a **version of the suite**, not about the
prose, and where the two disagree the suite wins.

## [Unreleased]

### Changed

- **An aggregate whose operands hold several different `#REF!` values
  carries one chosen by shape, then by name, never by row position** (§8;
  #115). The ranking is `cycle`, a name, `/0`, `empty`, `overflow`; among
  names, the one that sorts first by code point. A value that will not coerce
  is a name, so it outranks a stored cell beyond binary64. SPEC.md did not
  say, and both implementations carried the error of the first row in some
  cases, so swapping two lines changed an aggregate: `sum(c)` over a computed
  `#REF!(overflow)` and `#REF!(/0)` gave whichever came first, and the second
  implementation's `sum(a)` over a text cell and a cell beyond binary64 did
  the same. Both now follow the ranking, in table-level and per-row group
  aggregates. The ranking reads a `#REF!` as spelled, so a broken reference
  to a column named `cycle`, `empty` or `overflow` ranks as that shape.

- **`delta(c)` carries this row's error when this row and the preceding row
  both give one** (§7; #116). §7 now reads `delta(c)` as `c - prior(c)`, so
  §8's leftmost rule decides. SPEC.md did not say, and the two implementations
  disagreed: over a blank `c` after a stored cell beyond binary64, the
  reference gave `#REF!(c)` and the second implementation `#REF!(overflow)`.
  Both now give `#REF!(c)`. The reference also relabelled every error from a
  computed `c` as `#REF!(c)`; `delta` now carries the error `c` originated,
  such as `#REF!(/0)`, as §8 requires.

- **`key := fn(col)` is `malformed-declaration`, whatever `fn` is** (§4.1.11,
  §9.12; #110). `key := col` is `key`'s only form. The grammar generates
  `key := by(id)`, and SPEC.md did not say whether it was refused. The
  reference read `key := by(id)` and `key := sum(id)` as `key := id`, and read
  `key := sum(id where g = "a")` as an aggregate named `key`; the second
  implementation refused all three. The reference now refuses them too.

- **A CSV column name is trimmed of ASCII space and tab only before §9.2
  compares names** (§13; #118), as a key value is (§4.1.4). §13 did not say
  how a name was trimmed. CSV mode trimmed every Unicode whitespace character,
  so it refused `a` beside `a<U+00A0>` as `duplicate-column`; those are now
  two names. A header cell of spaces, one of a tab and an empty one are still
  one name, and two of them are still a duplicate.

- **Every §9 refusal has a stable identifier, and the suite asserts it**
  (#61). Each entry in SPEC.md §9 now opens with a name such as
  `duplicate-row-id` or `lone-cr`, and an implementation MUST report that
  identifier with the refusal; the message stays free. Refusing `parse` cases
  replace `refusal_contains` with `refusal`: one identifier where exactly one
  refusal applies, or a list of every identifier that applies where §9 leaves
  the choice to the implementation. Before this, 98 of the 116 refusing
  `parse` cases asserted `refusal_contains: ""` and passed on a refusal for any
  reason. The runner fails a refusing case that names no identifier, and a
  case still carrying `refusal_contains`.
  **This breaks every implementation that claims conformance and does not
  report identifiers**: it now fails every refusing `parse` case. The Python
  binding is the `refusal` attribute of the raised exception;
  `rowspec.Malformed` takes it as the keyword `refusal=`, so existing
  one-argument calls still construct. CSV mode does not report identifiers
  yet, and the CSV-profile cases in `conformance/cases-csv/` still assert
  `refusal_contains`; SPEC.md §13 says so. `conformance/cases/case-body.schema.json`
  lists the identifiers, so kindkit's case-tree validator refuses a misspelt
  one.

- **§9 lists `order-without-key`**, as entry 25. §6 has always required a
  `key` beside `order := by(c)`, and both implementations refused a table
  without one, but §9 — which says it is complete — did not carry it.

- **`key := col` must name a stored column, or it is `malformed-declaration`**
  (§9.12, §4.1.11, §6; part of #100). A key naming no column, or naming a
  computed one, had no §9 entry, and the two implementations disagreed: the
  reference accepted both and the second implementation refused both as
  `malformed-declaration`. The reference now refuses both too. No new
  identifier: the declaration names nothing a key can be, which is §9.12's
  ground.

- **§9 splits encoding into two entries: `bad-encoding` (§9.14) for bytes
  that are not UTF-8, and `leading-bom` (§9.26) for a leading BOM.** Both are
  decided on the bytes before any line is classified. Previously a leading
  BOM could also be read as the first character of line 1, so the reference
  implementation refused it as an unclassifiable line; the new wording rules
  that out. §13's CSV profile warns on `leading-bom` and refuses
  `bad-encoding`, as CSV mode already did. §9 also says how an identifier
  survives a split, a merge or a rename, and lists retired identifiers: none.

- **CSV mode refuses a stray quote** (#94). A `"` inside a field that does
  not open with one (`5" pipe`), or text after a closing quote (`"a"b`), is
  refused, as SPEC.md §13's reading of §9.6 and RFC 4180 §2. The csv module
  read both without complaint and guessed what the field held. Measured across
  2,063 files in three public data repositories: the first occurs nowhere, the
  second in one file.

- **xlsx export writes live formulas** (#35). The sheet holds a spreadsheet
  table named `rowspec`; computed columns are formulas over structured
  references, and declared aggregates are `SUBTOTAL` forms. Every operand and
  aggregate is guarded, so a blank operand, text in a summed column, or the
  minimum of nothing is a spreadsheet error rather than a `0`. What a
  spreadsheet cannot express is refused with `NotExpressible` and nothing is
  written: `cumulative`, `prior`, `delta`, any `where` predicate, an `if`
  comparing a number column against non-empty text, column names that differ
  only by case, a literal of more than 15 significant digits, and a table with
  no rows. `python -m rowspec_xlsx` reports a refusal on stderr and exits 1.
  The workbook recalculates under spreadsheet arithmetic. Tolerant
  comparison and subtraction can flip an `if` (#88), and left-to-right
  addition can cancel a `sum` or `avg` (#83). So it can disagree with
  `rowspec eval` beyond the last digit.

- **SPEC.md §13 states how the CSV profile reads four rules, and CSV mode
  now follows it** (#63). Each is a file that used to pass:
  - a quoted field still open at the end of the file is refused, where a CSV
    reader folds every later row into that one cell;
  - an empty line between rows is a record of one empty field (RFC 4180), so
    it is refused against a wider header instead of being skipped; a single
    empty line at the end of the file is still accepted;
  - a line whose first seven characters are a conflict-marker run is refused
    wherever it appears, as §4.1.12 says, a bare `=======` included;
  - with a key declared, an empty key value, or one holding whitespace or a
    `Cf` character, is refused. Only ASCII space and tab are trimmed first.

  §13 also records that column names, and key values apart from those three,
  are exempt from §4.1.9's allowlist in CSV mode, because the allowlist exists
  for formulas. That was already CSV mode's behaviour. Only a `Cf` character
  is still refused in a column name, so other look-alikes, such as an NBSP
  for a space, are not.

### Added

- **The mutation gate covers CSV mode** (#63, #94). `just mutants-csv` breaks
  `csvmode.py` and requires `conformance/cases-csv/` to notice: 33 mutants,
  one of them a control, are killed, 2 are claimed equivalent, with the
  reason, and none survive. It runs in CI and in the release gate. Eleven of
  the 33 first survived and waited, ungated: one was killed once stray quotes
  became a refusal (#96), and ten by the cases written from the spec for #94.

- **80 CSV-profile conformance cases** (#63, #94, #92) in
  `conformance/cases-csv/`, written from SPEC.md by authors who did not write
  CSV mode: 57 first, then 20 for the behaviours #94 listed, then 3 for a
  repeated empty column name (#92). They run in CI as `just conform-csv`, in
  the `conformance` job and in the release gate, with a floor of 80 cases.
  `conformance/cases-csv/README.md` records what each author was given and
  the questions the first left open.

- **28 conformance cases for the overflow, key and predicate fixes** (#100,
  #102, #107) in `conformance/cases/`, written from SPEC.md without the
  implementation. They pin `#REF!(overflow)` for infinite operands in
  aggregates and row expressions, the refusal of a `key :=` naming no stored
  column, a header group aggregate over a missing column, and predicate
  refusals behind an unknown name. The floor is now 438 cases.

- **The mutation gate covers those fixes** (#100, #102, #107). Eleven new
  mutants each undo one fix, and the cases kill every one of them on at least
  one wrong answer. Thirteen more cases from the same kind of author pin the
  leftmost unknown name in a predicate, predicate refusals behind a cycle or a
  missing aggregated column, and `cumulative` across opposite infinities. The
  floor is now 451 cases.

- **The exported workbook is checked against LibreOffice** (#36).
  `just test-libreoffice` recalculates every exportable `.mdtbl` in the
  conformance tree in headless LibreOffice. It asserts that each computed cell
  and aggregate matches `rowspec eval`, with a `#REF!` coming back as a
  spreadsheet error. The `xlsx-extra` CI job installs LibreOffice and runs it.
  The test pins each disagreement to the value LibreOffice gives:
  - four aggregates from the tree, where §7's exact sum is not a
    spreadsheet's sequential one (#83);
  - two tables written for the test, a branch flip under tolerant
    comparison (#88) and an ordinary-magnitude cancellation (#83).

- **The runner takes `--profile mdtbl|csv`** (#63). `csv` runs
  `conformance/cases-csv/`, a tree of its own for SPEC.md §13's CSV profile,
  against `rowspec.csvmode`; its one case kind, `check`, is described in that
  tree's README. The tree holds no case yet, so `just conform-csv` exits 2.
  `rowspec_alt` claims the `.mdtbl` profile only, and its commands now say so.

### Fixed

- **A stored cell spelled like an error value is text** (#126). SPEC.md §4.1
  rule 6 makes a cell that is not a `number` text, `#REF!(c)` as an operand
  of its own column `c`, and §7 lets only an error actually present poison
  `count`. The reference implementation read a stored `#REF!(zz)` as that
  error: `sum` and `count` over the column, and a row formula using it, gave
  `#REF!(zz)`, naming a column the table does not have. They now give
  `#REF!(a)` for the column `a` holding it, and `count` counts its row. A
  string comparison in `if` now compares it as the text it is. `rowspec_alt`
  already did all of this; a test now holds both to it.

- **`prior(c)` over a stored text cell is `#REF!(c)`** (#114). SPEC.md §4.2
  rule 10 leaves a computed value two kinds, a number and an error, and §8
  makes a value that will not coerce `#REF!`; blank is the one non-number §7
  lets `prior` carry. The reference implementation stored the text itself in
  the computed column, so `count` over that column counted it as a value
  where it must be poisoned. `rowspec_alt` already gave `#REF!(c)`; a test
  now holds both to it. `prior` over a computed column is unchanged here.

- **`prior`, `delta`, `cumulative` and an order column no longer trim
  U+00A0 and other Unicode spaces from a cell** (part of #114). SPEC.md
  §4.1.4 trims ASCII space and tab only. The reference trimmed again with
  Python's `str.strip()`, so a cell holding only U+00A0 was blank and
  `2<U+00A0>` was the number 2: `cumulative` summed it, an order column
  sorted it as a number, and a text order key lost the character. Each is
  now text, as in `rowspec_alt`.

- **A blank value in the key column is `bad-identifier`** (#111). SPEC.md
  §4.1.9 makes a key value an `ident`, one or more characters, so a blank
  one is not. The reference implementation accepted a table with one blank
  key and refused two as `duplicate-row-id`, as though two blanks were one
  id written twice. It now refuses both as `bad-identifier`, before any
  duplicate check. `rowspec_alt` already did; a test now holds both to it.

- **CSV mode no longer crashes on a header whose only repeated name is
  empty** (#92). The grouped-header check counted empty names, then took its
  label from the non-empty ones, and raised `IndexError` when there were
  none. Such a header is now refused as a duplicate column, because §13 makes
  an empty header cell a column name and §9.2 refuses two of one name.
- **A cell whose binary64 value is infinite is `#REF!(overflow)` as an
  operand in a row expression, not `inf` or `nan`** (#107). SPEC.md §8 makes
  such a cell `#REF!(overflow)` wherever it is an operand. The reference
  implementation passed it on: `a` and `-a` stored an infinity, `a - a`,
  `a * 0` and `a / a` stored `nan`, `if(a > 0, …)` picked a branch,
  `prior(a)` stored an infinity in the next row, `delta(a)` subtracted two
  into `nan`, and `cumulative(a)` went from `#REF!(overflow)` to `nan` after
  an opposite infinity. A numeric literal too long for binary64 — in
  arithmetic, as an `if` branch, or as a comparison bound — is
  `#REF!(overflow)` the same way. `count` over a computed column holding
  that error is now poisoned by it, as §7 requires. Because the infinite
  operand is now an error where it is read, §8's leftmost rule can pick it:
  `a + x` with `a` infinite and `x` blank was `#REF!(x)` and is now
  `#REF!(overflow)`, and so is `if(a > x, …)`. `rowspec_alt` already gave
  `#REF!(overflow)` in every one; a test now holds both to it.

- **An aggregate over a cell whose binary64 value is infinite is
  `#REF!(overflow)`** (#102). SPEC.md §8 makes such a cell `#REF!(overflow)`
  wherever it is an operand. The reference implementation passed it on. For
  `sum` and `avg`, `evaluate` raised `ValueError` when two infinities of
  opposite sign met, or `OverflowError` when the finite operands' partial
  sum also left binary64. For `min` and `max` it returned a silently wrong
  number whenever the result was finite: `min` over a positive infinity and
  `1` was `1`, and so was `max` over a negative infinity and `1`, in a
  declaration and in a header group aggregate alike. `count` is unchanged.
  `rowspec_alt` already returned `#REF!(overflow)`; a test now holds both to
  it.

- **`rowspec_alt` refuses an order column that is blank in every row** (#100),
  as `bad-order-column`. SPEC.md §9.10 refuses one that "is blank in any
  row"; `rowspec_alt` refused blank only when it was mixed with a value.

- **A header group aggregate over a column that does not exist is
  `#REF!(name)`, not a refusal** (#100). `| t = sum(nope where a = "x") |`
  was refused as `malformed-formula` by the reference implementation. SPEC.md
  §8 makes a name that does not resolve `#REF!(name)`, §4.2 rule 7 rejects
  refusing an aggregate over an absent column, and §9.20 does not reach a
  cell the grammar generates. The predicate's own refusals, such as
  `computed-column-compared`, still apply.

- **A refusal anywhere in a `where` predicate is reported even after a name
  that does not resolve** (#100). The reference stopped checking a predicate
  at its first unknown name and gave `#REF!(name)`, so
  `sum(a where zz = "x" and b = "x")`, with `b` computed, was accepted where
  §9.22 refuses it, and so was a right-hand side the grammar does not
  generate, such as `a = 3`. That held in header cells and in declarations.
  Every part is now checked first, and the leftmost unknown name is reported
  only if nothing is refused. `rowspec_alt` already did this.

- **A header group aggregate over a column on a cycle still has its
  predicate checked** (#100). The reference skipped an aggregate whose
  source column had no value yet, and a source on a cycle never gets one, so
  `| b = 1 + 1 | t = sum(u where b = "x") | u = t + 1 |` was `#REF!(cycle)`
  where §9.22 refuses it, and `sum(u where a = 3)` likewise where §9.20
  does. The predicate depends only on the header and is now checked first.
  `rowspec_alt` already did this.

- **A declaration over a missing column is still refused when the line
  breaks a rule** (#100). The reference returned `#REF!(name)` for
  `g := sum(nope ...)` before checking the function or the predicate, so
  `g := foo(nope)` was accepted where §9.11 refuses it, and so was a
  predicate §9.22 or §9.12 refuses. Both are now checked first.
  `rowspec_alt` already did this.

## [0.3.0] — 2026-10-08

Everything since `v0.2.0`. Documentation-only commits, and development and CI
changes with no effect outside this repository (#66, #67, #73), are not
listed separately.

### Added

- **An `eval-outcome` output on the action** (#72): `success`, `failure`,
  or `skipped` when `eval` is false or the action stopped before `eval` ran.
  A caller asserting that `eval` refused something should read it rather
  than the action's overall outcome, which is `failure` either way.

- **The action's default install path is exercised after every release**
  (#52). `release.yml` now calls `action-published.yml` once `publish`
  finishes. It runs the action exactly as a consumer does, with `install`
  left at its default, so it pip-installs the pinned release from PyPI. It
  asserts in both directions with the `eval: "false"` control. It can also be
  dispatched by hand. It does not run on pull requests, because a
  release-prep PR pins a version PyPI does not have yet.

### Removed

- **`conformance/corpus_check.py` and its CI step.** It looked for duplicate
  `id:` lines in `.md`, `.tbl` and `.canvas` files, and never opened a
  `.mdtbl` file, so it could not fail on anything this repository specifies.
  On this tree it printed `0 identified artifact(s), 0 duplicate id(s)`. A
  green step that measures nothing is a check that cannot fail.

### Changed

- **The conformance runner exits 2 when the implementation will not import**
  (#62). `conformance/run_cases.py` printed a traceback and exited 1, which
  its own docstring defines as "at least one case failed". It now prints a
  `HARD FAILURE:` line and exits 2, no verdict. `--help` names the `IMPL`
  argument.

- **The action pins `actions/setup-python` to a commit** (#71), as every
  workflow in this repository now pins its actions. The commit is the one
  the `v7` tag named, so what runs is unchanged. `tests/test_pins.py` fails
  if a floating `uses:` comes back.

- **The release gate runs `just test` and `just test-xlsx`, and the build
  checks `rowspec.__version__` against the wheel's metadata** (#69, #70).
  The 0.1.0 wheel shipped `__version__ = "0.0.0"`, and the tagged commit was
  held to the pytest suite only by the PR checks before it.

- **Source files carry SPDX headers**, and `tests/` and `conformance/reserved/`
  have their own `LICENSE` (#74). Two paths are relicensed, both to more
  permissive terms, and three that named no licence now name one:
  - `conformance/reserved/` is CC0-1.0, like `conformance/cases/`. It had no
    `LICENSE` of its own, so it was MIT, from `conformance/LICENSE`.
  - `docs/ci/rowspec-check.yml`, the CI template users are told to copy, is
    CC0-1.0. It was CC-BY-4.0 with the rest of `docs/`.
  - The root `LICENSE` now lists `action.yml`, `.github/workflows/` and the
    `justfile` under Apache-2.0 OR MIT.

  `tests/test_licensing.py` checks the headers and the `LICENSE` files.

- **The `reference/` standard-library-only check sees dynamic imports**
  (#65): `__import__("x")` and `importlib.import_module("x")` with a
  constant name.

- **CI runs the suite, the second implementation and the mutation gate
  through kindkit's reusable workflow.** A new `kind` job in `check.yml`
  calls `kindspec/kindkit/.github/workflows/kind.yml` at `8e21b55`, the same
  commit the `dev` group pins. It reports as `kind / conformance` and does
  more than the steps it replaces. It checks the case tree against kindkit's
  convention. The suite and the second implementation pass only if they ran
  every case directory under `conformance/cases`, read from that root. The
  mutation gate is judged by the gate's own report, not by its exit code.
  `just conform`, `just conform-alt` and `just mutants` are no longer steps of
  the `conformance` job. That job keeps its name and everything else: lint,
  `just test` with the extra absent, and the example recipe. `just test` still
  runs the suite and the gate too, through `tests/test_conformance.py`, as it
  did before. The `kind` job is not a replacement for those tests.
  `tests/test_pins.py` fails if the workflow's kindkit commit and the
  package pin differ.

- **kindkit pin moved to `8e21b55`** (from `bf716e3`), kindkit's main after
  its reusable workflow landed (kindkit#24). kindkit has no tag past
  `v0.1.0`, so the pin is a commit. The new kit adds what that workflow
  reads: the runner's report names the `root` it read, the runner takes its
  report path from `KINDKIT_REPORT_JSON`, and `gate()` writes its verdicts
  to `KINDKIT_GATE_REPORT`. It also makes the merge helper raise on a failed
  git call and dates each scratch write with its own mtime. No rowspec code
  changes: `conformance/mutants.py` already probes through `probe_command`,
  which now carries `root` through. Measured: `just check`, `just conform`,
  `just conform-alt` and `just mutants` print output identical line for line
  to the previous pin's (0 failures across 410 cases on both
  implementations; 73 killed, 0 survived, 2 equivalent, 0 stale, 0 broken),
  and `just test` differs only in its wall time.

- **The mutation gate has 75 mutants, all distinct, and refuses duplicates**
  (#48). Two `(old, new)` pairs were each in the table twice, so 76 mutants
  were 74 distinct mutations. `count-ignores-blanks` repeated
  `the-blank-route-empties-count-too` and is removed.
  `CONTROL-drop-every-third-row` repeated `drop-every-third-row`, so it could
  not fail independently of it. It is replaced by
  `CONTROL-parse-reverses-every-row`, which patches a line no other mutant
  touches. `just mutants` now prints 73 killed, 0 survived, 2 equivalent, 0
  stale, 0 broken. Every other mutant's verdict and killing cases are
  unchanged. The gate exits 2 if two mutants produce the same mutated source,
  however their patterns are spelled.

- **CSV mode warns on a lone CR** (#59). SPEC.md §13 makes refusal 15 (a
  lone `CR`) a warning in CSV mode; `rowspec check` passed one silently. Under
  `--strict` it is refused, like the BOM and `CRLF` warnings. The `CRLF`
  warning is unchanged and now says it is rowspec's advisory: SPEC.md §3
  accepts `CRLF`, and `docs/csv.md` no longer says §3 requires `LF`.

- **kindkit pin moved to `bf716e3`, the commit kindkit's `v0.1.0` tag names.**
  From `a26f8f8` the only package change is one docstring. The pin stays a
  commit rather than the tag, because a tag can be re-pointed. Measured: 0
  failures across 410 cases on both implementations, and `just mutants` output
  identical line for line to the previous pin's (74 killed, 0 survived, 2
  equivalent, 0 stale, 0 broken).

- **The mutation gate's probe reads a JSON verdict, not the runner's prose.**
  kindkit pin moved to `a26f8f8` (kindkit#16). `conformance/mutants.py` now
  calls `kindkit.probe_command`, which runs the suite with `--report-json` and
  reads back which cases ran and which failed. The two regexes that parsed the
  printed summary are gone, and the kit now refuses a failing case id that did
  not run. Measured: the gate's output is identical, line for line, to the
  previous pin's, and a reworded summary line no longer costs the probe its
  verdict (the old probe exited 2 under it).

## [0.2.0] — 2026-10-07

Everything since `v0.1.0` (`625ddb2`); documentation-only commits are not
listed separately.

### Added

- **A GitHub Action** (`c19538a`) running both `check` and `eval`, with a
  self-test that asserts in both directions: that it fails a well-formed table
  whose total is `#REF!`, and that the same file passes with `eval: false` — so
  the first assertion is about `eval` and not about the file.

- **An `install` input on the action** (#51), defaulting to the pinned release,
  which `release.yml` checks matches the tag being released. The self-test sets
  it to `.`: until then it installed the pinned wheel from PyPI, so a regression
  in a pull request's own code could not turn either required self-test job red.
  Watched red both ways on the branch — `eval` exiting 0 on a broken total, and
  `eval` exiting 1 on a good tree. The default install path is no longer
  exercised by any job (#52).

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

- **kindkit pin moved to `e2aa334`** (from `d5cb216`). The merge cases now
  run git with the developer's configuration stripped out (kindkit#13).
  Measured: with `* merge=union` in `~/.config/git/attributes`, the old pin
  fails 4 merge cases (`git said clean, expected conflict`) and the new pin
  fails none. The gate also now purges cached bytecode under
  `PYTHONPYCACHEPREFIX` (kindkit#14), which closes a stale-bytecode hole in
  `conformance/mutants.py`'s subprocess probe; that hole was not reproduced
  here.
  Re-measured on the new pin, every figure is unchanged: 0 failures across 410
  cases on both implementations; 74 killed, 0 survived, 2 equivalent, 0 stale,
  0 broken; 52 passed, 1 skipped.

- **The runner has three exit codes, not two**: 0 every case passed, 1 at least
  one case failed, 2 the fixture tree yielded no verdict at all. A missing
  root, an empty root, and a root that has shrunk below the 410 cases `find
  conformance/cases -name expect.json | wc -l` reports are all the third thing.
  "Every case passed" and "no case ran" no longer look alike from the outside.

### Fixed

- **`rowspec.__version__` reported `0.0.0`**, in the published 0.1.0 wheel
  too. It now matches the package version.
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

  **The size precondition is present; the timing one is not, and no real gate
  run reaches the window.** Both halves are measured, and the second is why
  this is a hazard closed rather than a wrong result corrected.

  Applying all 76 mutants and measuring `len(out.encode())` gives **14 groups
  of mutants that produce byte-identical file sizes**, the largest holding
  five. `strip-eats-non-ascii-spaces`, `allow-duplicate-order-declaration` and
  `order-accepts-any-function` are one such group — all three 49,765 bytes
  against an unmutated 49,770 (`wc -c reference/rowspec/table.py`). Two of
  those groups are even **adjacent in table order**, so the sizes collide in
  the position that matters.

  What does not collide is the clock. Instrumenting the gate to `stat` the
  scratch file after each of its 77 writes: **minimum inter-write gap 1.368 s,
  mean 1.804 s, no gap under 1 s**, and **0 pairs across the whole run share
  both a whole-second mtime and a size**. A 410-case probe simply takes too
  long. So the defect has never fired in a real run here, and the numbers this
  gate has published were never at risk — which is exactly what makes it worth
  fixing now rather than after someone makes the probe faster.

  Watched red on two of those mutants, unmodified, through a deliberately fast
  probe over the same adapter and two real fixtures, because that is the only
  way to reach the window:

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
  `timeout 15` without it, and refuses in 3s with `PROBE_TIMEOUT` lowered to 3
  for the demonstration. The shipped value is 300s; the 3s figure is not
  reproducible from the committed constant, and saying so is cheaper than a
  reader discovering it.

- **`just test` had never run in CI.** The conformance suite and the mutation
  gate did, through `just conform` and `just mutants`, so the gap was invisible
  — but `tests/` also holds the CSV refusals and the CLI's own behaviour, and
  nothing on a forge ran them. It now runs with the xlsx extra deliberately
  absent, behind a step that asserts the extra really is absent.
- The mutation gate took its paths from the working directory, so it reported
  differently depending on where it was invoked from (`c0b9a7a`, closes #31).
  Paths are now anchored to `__file__`.

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
- **The mutation gate** — 76 mutants, of which **74 are distinct mutations**:
  two `(old, new)` pairs appear twice, so `74 killed` is 72 distinct kills.
  Pre-existing and tracked in #48; the figure is stated rather than quietly
  published. A surviving mutant is a failure and so is
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

[Unreleased]: https://github.com/kindspec/rowspec/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/kindspec/rowspec/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/kindspec/rowspec/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kindspec/rowspec/releases/tag/v0.1.0
