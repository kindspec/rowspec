# Why this case exists

§4.2 rule 10's static analysis, with the cycle spread over two columns rather
than closed inside one. `x` names `y` only in its unselected branch and `y`
names `x`; `c` is positive in the single row, so no evaluation ever traverses
the edge that closes the loop.

Rule 9 already fixes the value: "**A cycle evaluates to `#REF!(cycle)`**, in
every column on the cycle and in every column whose formula depends, directly or
transitively, on one." Rule 10 fixes that the edge `x → y` exists at all, since
it lives in a branch: "Dependency and cycle analysis is over the whole formula,
both branches included".

An implementation that builds its dependency graph from the *selected* branch
sees `x` depending on nothing and `y` depending on `x`, an acyclic graph, and
reports `1` for both totals. A self-cycle (`x = if(c > 0, 0, x)`) can be caught
by an evaluator that merely notices re-entry into the cell it is computing; this
one cannot, which is why both files exist.
