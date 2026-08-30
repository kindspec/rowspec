# Why this case exists — and it FAILS

§4.2 rule 10 scopes the blank test to a **cell**: "it is the one place in the
format where a **blank cell** is data rather than an absence. A **blank cell's**
text is the empty string, so the equality is true."

`nope` is not a blank cell. It is not a cell at all — no column of that name
exists — so §8 applies unchanged: "A reference to a name that does not exist
evaluates to `#REF!(name)`", and rule 10's amended paragraph confirms the
comparison inherits it: "An error operand is an error under every operator, `=`
and `<>` included ... It is *not* treated as blank."

**The reference implementation returns `1.0`.** The two absences look identical
from inside it and the format treats them oppositely. A blank cell is an *absent
value* and the blank test is true. A missing column is an *absent name* and the
blank test is an error.

The single cell is asserted here so the failure names it. The full extent of the
defect — the same wrong answer under `<>` and under a non-empty string, and the
three neighbouring paths that are correct — is in
`eval/if-text-comparison-on-a-missing-column-is-still-an-error`, whose WHY.md
carries the measurements and the argument that the implementation, not the
spec, is wrong.

§9.22 does not reach this file: that clause is scoped to a left-hand `ident`
naming a **computed** column, and `nope` names nothing. The construct is
well-formed and the assertion is on the value, which is where the finding lives.
