# Why this pair exists

§4.2 rule 10: "**a `cond`'s parenthesis counts toward §9.23's limit of 64
exactly as a bare one does — the recursion is the same recursion, since `cond`
is reached through `primary`**". §9.23: "an `expr` nesting parentheses more than
**64** deep".

So 64 nested `if`s are accepted and 65 are refused, and this pair pins the
number rather than merely pinning that *some* number exists.

**The parenthetical in rule 10 was added because of this pair.** §9.23 predates
`if` and its example is a run of bare parentheses; an implementer who counts
only the `"(" *WSP expr *WSP ")"` alternative of `primary` accepts an
arbitrarily deep nest of `if`s and gets the outcome §9.23 exists to prevent — "a
reader whose limit is its host's call stack accepts at 230 and crashes at 250,
and two such readers refuse different files for reasons neither documents". The
recursion is identical; only the spelling differs, and a limit that is a
function of the spelling is not a limit.

**The pair is the test.** A single refusal case pins only that some depth is
refused and keeps passing if a reader draws the line at 8 or at 4096, which is
the finding `parse/nesting-depth-65-refused` records for the bare-parenthesis
form. Two cases either side of the number pin the number, and they must be
written for `cond` separately because a reader can count one construct and not
the other.
