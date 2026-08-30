# Why this case exists, and what it does NOT catch

§4.2 rule 9: "A formula may name any column, stored or computed, wherever that
column stands in the header. **The order of columns in the header is not an
input to any value**". `x`'s comparison names `y`, which is computed and stands
to `x`'s *right*, so this is a forward reference through a `comparison` — the
position rule 9's own example (`| net = qty * unit | gross = net * 1.2 |`) does
not cover, since rule 9 predates `if`.

`r_02` has `a = -5`, so `y` is `-10`, the comparison is false, and `x` is `2`.
Under left-to-right evaluation `y` is unresolved when `x` is computed and the
answer is `#REF!(y)` or, worse, whatever the reader's default is. Rule 9 is
explicit about the cost: "the header's column order becomes a coordinate, and
moving a column, which §10's canonical form otherwise treats as a pure
rearrangement, changes a total."

**Now the honest part, which is the reason this WHY.md is longer than the case.**
This case looks like it should also catch an implementation that omits a
comparison's names from its dependency graph, and it does not. An evaluator that
iterates its plain-formula pass to a fixpoint — which any implementation with a
row-relative and a group-aggregate stage has to do, since those stages run
between the plain passes — repairs a missing dependency edge for free on the
second pass: the first pass computes `x` with `y` unresolved, the pass computes
`y`, and the next pass recomputes `x` against the now-correct `y`. The wrong
answer is transient and never observed. A missing edge is only observable where
iteration cannot converge on the right answer, which is a **cycle** —
`eval/if-cycle-through-a-comparison-lhs-is-static` and
`eval/if-cycle-through-an-ordering-rhs-is-static` are those cases.

The case is kept anyway, because rule 9's guarantee is worth pinning on its own
terms and because an implementation with a single non-iterating pass — a
topological sort, which rule 9 explicitly permits as "a free choice" — fails it
outright.
