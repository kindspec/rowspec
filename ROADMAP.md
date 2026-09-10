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
    0 broken                  just mutants
    52 passed, 1 skipped      just test

The second implementation is the load-bearing one. `reference/rowspec_alt/` was
written from `SPEC.md` alone by an author forbidden to read `reference/rowspec/`
and runs against the same fixture tree in CI on every push. On the last three
questions where the two disagreed, the independent implementation was right.

## Next

### 0.2.0 — rowspec on kindkit — **landed**

The runner and the mutation gate are now
[kindspec/kindkit](https://github.com/kindspec/kindkit), and rowspec is its
first consumer (#33). The point was not tidiness: blockspec and nodespec would
otherwise each re-derive them, and this project has twice caught duplicated
implementations drifting apart invisibly. kindkit is a dev dependency pinned to
a commit — vendoring a copy would have been the drift the kit exists to
prevent.

**The abstraction fit.** Every acceptance number is identical before and
after, and so is every individual verdict: the same kill, the same equivalence
and the same killing cases for all 76 mutants. `rowspec check`, `rowspec eval`,
the fixture tree layout and the Action's inputs are unchanged, and not one of
the 410 cases was edited. What the kit could not be told about rowspec — what a
`parse` case means, what a `canon` check asserts, how the merge sides are filed
— stayed in rowspec, which is where the line was supposed to fall.

It also closed three open defects rowspec had and the kit did not: an orphaned
equivalence claim (#37), a stale `.pyc` crediting a mutant with its
neighbour's verdict (#44), and a mutant that crashes the runner before any case
opens being scored as killed (#45).

**The bar was pre-registered, and it stays written down.** What this milestone
committed to before the work ran was: *if the abstraction does not survive
contact with a single example, the honest outcome is to say so and keep the kit
as documented convention. A kit designed around one consumer is a kit fitted to
that consumer.* It survived, on every number. Recording the criterion next to
the result is the point — a bar that is deleted once it is cleared is a bar
that could have moved.

**And the second half of it is still open.** rowspec is the only consumer.
"Fitted to that consumer" cannot be answered until blockspec or nodespec runs
on the kit, and nothing here settles it.

**This is load-bearing**, so it takes more than one independent review pass.

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
evaluate **8,417 corpus cells across 70 distinct expressions**. The six
arithmetic functions the obvious response would add — `ROUND`, `ROUNDDOWN`,
`INT`, `MIN`, `MAX`, `CEILING` — are 4,362 of those cells and **nine distinct
expressions between them**: six functions of permanent, twice-implementable
surface area, for nine formulas. `ROUNDDOWN` alone is 2,052 cells and *one*
expression, a bowling average filled down a column in a problem the corpus ships
six times.

**Only one entry in the gap has any breadth, and it is not a function**:
`If:text-branch`, 2,602 cells over 29 distinct expressions. It is the largest
single blocker and the only candidate whose evidence is breadth rather than
replication — and if the ceiling is ever raised it should be argued on its own
terms, with its own measurement, not folded in beside six arithmetic functions.
It needs a bigger *value model*, not a bigger grammar, which is a different and
much more expensive change. See `docs/rationale.md`, "The formula
ceiling is deliberate", and `research/design-findings/E6-formula-ceiling.md`.

Do not quote the pre-`if` figures for this. The earlier "21,165 cells outside
the grammar, `IF` 12,643 and `SUM` 5,552" was arithmetic over function-name
counters, and `research/design-findings/E4-if-sum-shapes.md` §4 retracts it:
`SUM` would admit **51**, not 5,552, because 5,861 of its 5,912 cells (99.1%)
are already expressible today — 3,485 as `a + b + c` under §4.2, and 2,376 as a
§7 aggregate declaration, neither of which needs new grammar. `if` has since
shipped. And the count is cells, which #28 shows is inflated ~6x by replication.

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
