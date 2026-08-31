# Why this case exists

§4.2 rule 10: "a `cond`'s parenthesis counts toward §9.23's limit of 64
exactly as a bare one does — the recursion is the same recursion, since
`cond` is reached through `primary`."

The twin of `parse/mixed-if-and-paren-nesting-depth-64-accepted`: 33 bare
parentheses alternating with 32 `if(`s, total depth 65, refused (§9.23). An
implementation keeping two separate depth counters — one for bare parens, one
for `cond` — sees 33 and 32, both under 64, and accepts a file the spec
refuses. Together the pair is only passed by counting every nesting level
once, whatever construct opened it.
