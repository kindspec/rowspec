# Why this case exists

§8: "**That precedence is transitive**: a column that merely *depends* on a
cycle, and separately names something absent, is also `#REF!(cycle)`" — and,
one paragraph later: "**Cycle precedence outranks the leftmost rule,
wherever the two disagree.** In `| z = nope + x |` with `x` on a cycle and no
column `nope`, the leftmost unresolved name is `nope` and the answer is still
`#REF!(cycle)`."

That second sentence is this exact formula. `eval/cycle-beats-missing-name`
pins the precedence for a column ON the cycle; here `z` is not on the cycle
`x = y | y = x` — it only depends on `x`, and the absent name comes FIRST in
its text. An implementation that resolves names first and reports the
leftmost miss answers `#REF!(nope)`, passes the leftmost cases and the
on-cycle case, and fails only here. The cycle must win even from second
position and one step removed, because "the cycle is the thing that must be
fixed first" — adding a column `nope` would change nothing.
