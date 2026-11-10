<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# What has been measured

## What it does not do, measured

**If your table is a list of facts, you probably do not need this.** We replayed
7,446 real commits from four public CSV-in-git registries, including 528 real
three-way merges. Neither `.mdtbl` nor plain CSV ever merged silently wrong.
For an ordinary sorted registry CSV, **stock git already does what this format
promises**, and none of those maintainers has wanted a computed column in four
years.

The format earns its keep when a table **computes** — when a merge can leave a
total that is quietly wrong, which is the failure a CSV cannot even represent.

**Two branches each adding a column conflict badly**, across most of the file.
That is inherent to one-row-per-line and it is exactly what happens to a CSV.
Nothing here fixes it; a column addition rewrites every row either way.

**It is not a data-quality tool.** Whether a country code is in ISO 3166,
whether a URL resolves, whether a date is plausible — none of that is here, and
[Frictionless](https://frictionlessdata.io/) does it well. rowspec asks a
smaller question: will this table survive being edited by several people over
years?

**Keeping rows in key order has a measured cost.** Across those 7,446 commits,
367 (4.93%) reorder rows against every parent, and 457 (6.14%) against at least
one, the difference being merges that bring in a reorder already counted on its
branch. The median such commit moves 1 to 4 rows, depending on the registry, and
none moves more than half a file (`experiments/D0-dogfood/reorder.py` in the
research repository). The current file of all four registries is out of key
order (`reorder-results.txt` beside it): a key-only sidecar means sorting once
and keeping new rows in place, and a file kept sorted by another column declares
that column as `order`.

## What is actually shipped

The **conformance suite** is the deliverable. It checks out two branches, runs
stock `git merge`, evaluates the merged file, and asserts on the computed
number. No prior art does this. The spec, the validator and the reference
implementation exist so the suite has something to check.

    703 conformance cases          two implementations, both passing
    122 mutants, all distinct      119 killed, 3 equivalent
                                     0 survived, 0 stale, 0 broken

**The second implementation is the point.** `reference/rowspec_alt/` was written
from `SPEC.md` alone by an author forbidden to read `reference/rowspec/`, and it
runs against the same fixture tree in CI on every push. It is the only evidence
that this document *defines* the format rather than describing one program, and
it has repeatedly been the half that was right: on the last three questions
where the two disagreed, the independent implementation was correct and the
reference was wrong.

**The mutation gate is the other half.** The suite is only worth its green tick
if it can go red, so the implementation is deliberately broken in 118 specific
ways. 116 must be caught by a case; the other two carry a recorded claim that no
input could distinguish them from the original, and the gate fails the run if a
case turns out to catch one anyway. No two mutants produce the same mutated
source, and the gate refuses to run if two do. A mutant that survives is reported as a
failure, and so is a *stale* one whose pattern no longer matches the source —
because a check that quietly stopped running is the failure this project keeps
finding in itself.

**Both are [kindkit](https://github.com/kindspec/kindkit)** — the shared
machinery rowspec and blockspec run on. What lives here is the part that knows
what a rowspec case means; walking the tree, reading fixtures as exact bytes,
splicing mutants and accounting for the verdicts are the kit's, and rowspec is
its first consumer.

Neither number is a claim about correctness in general. See
[rationale.md](rationale.md) for what has been measured, and what has
been measured and found wanting.
