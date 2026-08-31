# Why this case exists

§7: "`cumulative(c)` is `#REF!(c)` from the blank row **onward**, by ordinary
propagation."

This is the sharpest single cell in the family. An implementation that skips
the blank row reports `12.0` here — a plausible running total, on a row whose
own cell holds an ordinary `7`, with nothing else in the table looking wrong.
That is exactly the stale value §8's "never evaluates to zero, empty, or a
stale value" forbids, and it is the cell where the historical divergence
between implementations lived: a guard that notices the blank row itself but
*resumes* the total afterwards passes every assertion except this one.

All six `rowrel/*-blank-row-*` cases share one input — rows `5`, blank, `7`
under `order := by(day)` — and each asserts ONE cell, because a `rowrel` case
asserts one cell and the three operators fail this input in three different
ways. One `eval` case aggregating over the computed columns could not separate
them: every aggregate over `run`, and over `chg`, is `#REF!(amt)` under any of
the plausible wrong behaviours too, so an aggregate-level assertion cannot
tell a conforming reader from one that stepped over the blank. The per-cell
family can.
