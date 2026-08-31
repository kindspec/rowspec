# Why this case exists

§4.2 rule 10: "a `cond`'s parenthesis counts toward §9.23's limit of 64
exactly as a bare one does — the recursion is the same recursion, since
`cond` is reached through `primary`."

`parse/nesting-depth-64-accepted` pins the limit for bare parentheses and
`parse/if-nesting-depth-64-accepted` pins it for `if` alone; this case and
its 65-deep twin pin that the two share ONE counter. The formula alternates a
bare `(` and an `if(` all the way down — 32 of each, total depth 64. An
implementation that double-counts a `cond` (its `(` and the `cond` node
both) sees depth 96 and refuses this file, which the spec accepts.
