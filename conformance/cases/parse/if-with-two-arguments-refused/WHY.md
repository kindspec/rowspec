# Why this case exists

`cond` has exactly three parts and both commas are required. There is no
one-armed `if` in §4.2 and §9's list has no entry that would supply a default
for the missing branch.

The wrong outcome is not a parse error but an invented value: a one-armed `if`
whose condition is false has to produce *something*, and the candidates are
`0` — which §8 forbids in the strongest terms, "A broken reference never
evaluates to zero, empty, or a stale value" — and a blank, which §5 reserves for
stored cells of computed columns and §10 would then have to canonicalise. Both
are exactly the "plausible number, no diagnostic" shape §1 exists to remove.
