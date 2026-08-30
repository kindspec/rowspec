# Why this case exists

§4.2 rule 10: "**Dependency and cycle analysis is over the whole formula, both
branches included, and is not affected by which branch a row selects.**
`| x = if(c > 0, 0, x) |` is `#REF!(cycle)` in every row, including rows where
`c` is positive and the cycle is not reached."

Row `r_01` is exactly that row. It is asserted as a single cell, not as a total,
because a total mixes it with `r_02` — where even a data-dependent
implementation finds the cycle — and the whole finding here is the row where the
cycle is *not* reached.

This is the subtlest sentence in rule 10, and it is deliberately in tension with
the sentence three paragraphs above it: **evaluation is lazy and analysis is
not.** An implementation that unifies the two — the natural thing to write,
since a lazy evaluator already knows which branch it took — returns `0` here and
`#REF!(cycle)` in `r_02`, which is a column whose cycle-hood is a function of
the data. Rule 10 states the cost of that directly: "adding one row could turn a
working table into a cyclic one, and two branches inserting different rows could
disagree about whether the table has a cycle at all".

There is no other legitimate resolution; the spec names the alternative and
refuses it.
