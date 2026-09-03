# Roadmap

Where rowspec is, and what is next. Superseded
[PLAN.md](https://github.com/kindspec/research/blob/main/PLAN.historical.md),
which was the bootstrap plan and is now historical.

Numbers here are measured, not remembered. The figures under **Where it is**
name the command that produces them; the corpus figures below cite the
measurement in [kindspec/research](https://github.com/kindspec/research) by
path.

## Where it is

**Draft 0, released as `v0.1.0`**, on PyPI, with a GitHub Action.

    410 conformance cases     find conformance/cases -name expect.json | wc -l
    0 failures                just conform
    0 failures, second impl   just conform-alt
    74 killed, 0 survived     just mutants
    2 equivalent, 0 stale     just mutants
    44 tests passed           just test

The second implementation is the load-bearing one. `reference/rowspec_alt/` was
written from `SPEC.md` alone by an author forbidden to read `reference/rowspec/`
and runs against the same fixture tree in CI on every push. On the last three
questions where the two disagreed, the independent implementation was right.

## Next

### 0.2.0 — rowspec on kindkit

The runner, the mutation gate and the case-tree convention become
[kindspec/kindkit](https://github.com/kindspec/kindkit), and rowspec becomes its
first consumer. The point is not tidiness: blockspec and nodespec would
otherwise each re-derive them, and this project has twice caught duplicated
implementations drifting apart invisibly.

**Compatibility.** Internals move freely. `rowspec check`, `rowspec eval`, the
fixture tree layout and the Action's inputs do not change. The suite must be at
410/410 on **both** implementations and the gate at 0 survivors and 0 stale
before and after — the same numbers, not merely green.

**This is load-bearing**, so it takes more than one independent review pass.

If the abstraction does not survive contact with a single example, the honest
outcome is to say so and keep the kit as documented convention. A kit designed
around one consumer is a kit fitted to that consumer.

### 0.2.0 — export to `.xlsx`

The strongest downstream story and the only unstarted milestone from the
bootstrap plan. Verified in design as essentially lossless with real structured
references and `SUBTOTAL` aggregates recalculating in LibreOffice.

**It lives outside `reference/`, as an optional extra.** `AGENTS.md` makes
`reference/` standard-library-only because *a dependency there is a dependency
every independent implementation inherits* — and an independent implementation
of a table format must not be required to read xlsx. Export ships as
`rowspec[xlsx]` with its own tests and its own dependency.

The round-trip claim is only worth stating if it is checked against a real
spreadsheet application, so the test asserts on values recalculated by
LibreOffice, not on bytes we wrote.

## Open, and deliberately not rushed

**`#REF!(name)` conflates two facts** — a name that does not exist, and one
whose cell is blank — 16,953 cells, 30.4% of the differential's comparisons
(`research/design-findings/E1-differential-eval.md`). Splitting it changes §8's
error vocabulary, which is why it is not being rushed. See `docs/rationale.md`,
"Adding `if` was a measurement", and `SPEC.md` §8.

**The formula ceiling.** Measured against 5,526 real workbooks, `.mdtbl` cannot
evaluate **8,417 corpus cells**. The six functions those cells most name —
`ROUND`, `ROUNDDOWN`, `INT`, `MIN`, `MAX`, `CEILING` — are 4,362 of them and
**nine distinct expressions between them**. The ceiling is deliberate; see
`docs/rationale.md`, "The formula ceiling is deliberate", and
`research/design-findings/E6-formula-ceiling.md`.

Do not quote the pre-`if` figures for this. The earlier "21,165 cells outside
the grammar, `IF` 12,643 and `SUM` 5,309" was arithmetic over function-name
counters and `research/design-findings/E4-if-sum-shapes.md` §4 retracts it: `SUM`
would admit 51, not 5,309, because 99.1% of its cells are already `a+b+c` in
§4.2 today. `if` has since shipped. And the count is cells, which #28 shows is
inflated ~6x by replication.

**Composite keys.** 31.5% of real `INDEX` usage (`research/PLAN.historical.md`
§5); `key := col` takes one column. `key := (region, sku)` is small but touches
merge.

**§12 editions have no observable behaviour.** Specified, unimplemented,
untested. It is the one part of the spec that has never been exercised.

**2-D matrix lookups** — 17% of real `INDEX` usage (`research/PLAN.historical.md`
§5), wide by construction, and
with no long-form equivalent. Probably out of scope forever, and *saying so
explicitly* is the deliverable, not building it.

## Not planned

Real-time collaboration. A merge server. Import from `.xlsx`. Any GUI. The
document and canvas kinds, which are [blockspec](https://github.com/kindspec/blockspec)
and [nodespec](https://github.com/kindspec/nodespec).

**And do not lead with the merge.** Demand for merge tooling is measurably
absent — a 230:1 give-up-to-hack ratio (`research/design-findings/X7-demand-verdict.md`),
and GitHub archived its own version.
Lead with the validator and the spec. Correct merging is a property you get, not
a reason anyone adopts it.
