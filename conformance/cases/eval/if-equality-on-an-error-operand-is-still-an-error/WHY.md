# Why this case exists

§4.2 rule 10, as amended: "**An error operand is an error under every operator,
`=` and `<>` included.** If the left-hand column holds a `#REF!` of any shape,
the whole `cond` is that error and the row's cell carries it, with the
originating name preserved by §8. It is *not* treated as blank."

`e` is `#REF!(/0)`. Both comparisons must carry that exact value through — not
`#REF!(e)`, which §8 reserves for a name that could not be resolved, and not a
fourth or fifth spelling, since §8 now fixes the count at four.

The right-hand side is the `literal` `0` rather than a `string`, and that is
deliberate: §9.22 refuses a `string` right-hand side against a computed column,
so the numeric spelling is the only one that reaches this rule at all through a
computed column. Rule 10 explicitly keeps the numeric form legal — "A
**numeric** right-hand side carries no such restriction".

Rule 10 names the failure mode it is guarding: "the blank test below invites the
opposite reading — 'the operand produced no number, so call it blank' — under
which a `#REF!(/0)` cell silently tests equal to `""` and a division by zero
becomes the author's missing-data fallback." Under that reading `m` is `1`, `n`
is `0`, and both totals are numbers. `sm` and `sn` are asserted together because
`=` and `<>` fail it in opposite directions and an implementation that got one
right by accident would still lose the other.

**This case is the replacement for one that no longer parses.** It was first
written as `if(e = "", …)` — the blank test on an error — which was the most
direct statement of the rule. §9.22's new clause refuses that spelling outright,
because `""` is a `string` and `e` is computed, and rule 10 is right that it was
never a useful comparison: a computed cell is never blank, so it could not have
fired. The rule survives the spelling; `= 0` reaches it.
