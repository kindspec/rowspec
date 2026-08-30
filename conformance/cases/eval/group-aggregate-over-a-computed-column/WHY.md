# Why this case exists

This is the bill of materials from the cold-use trial, with the numbers it
should have produced. Every `vendor_total` cell evaluated to `0`, `check`
reported `0 refused` and exit 0, and the true subtotals were 17.75 / 4.87 /
7.00. It was committed before anyone noticed, and caught only by hand-checking
totals — the labour the tool exists to remove.

§4.2 rule 5 is explicit that this is well-formed: "The aggregated column itself
carries no such restriction: `sum(total where region = @region)` over a computed
`total` is well-formed and rule 9 gives it a value." Here the aggregated column
`ext_cost` is computed (`qty * unit_cost`) and the predicate's idents (`vendor`)
are stored, which is exactly the shape rule 5 permits.

§8 is what makes the old behaviour a defect rather than a limitation: "A broken
reference never evaluates to zero, empty, or a stale value."

All five aggregates are asserted together on purpose. In the failure only `sum`
returned a plausible number; `min`, `max` and `avg` returned `#REF!` loudly and
`count` was right by accident. The one function everybody uses for money was the
one that lied, and a case that pinned only `sum` would not have shown that the
other four were the reason anyone could tell.
