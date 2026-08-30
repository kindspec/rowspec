# Why this case exists

§4.2 rule 10: "**Dependency and cycle analysis is over the whole formula, both
branches included**". The *whole formula* includes the `comparison`, which is
where this cycle lives — neither branch mentions `x` at all.

`rowrel/if-cycle-is-static-in-a-row-that-avoids-it` puts the cycle in a branch,
which is the case rule 10 prints. An implementation that reads that sentence as
"walk the branches" — the branches being the new thing `if` introduced — builds
a dependency graph for this column from `1` and `0`, finds no edges, and then
has to evaluate `x > 0` while computing `x`. What it does next is
implementation-defined and none of the options is `#REF!(cycle)`: re-entry
guards give a blank or a zero, a fixpoint gives whatever the seed was, and a
memo gives the partial value.

The condition is not an optional part of the formula, and the rule says
"formula", not "branches".
