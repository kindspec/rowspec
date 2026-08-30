# Why this case exists

§4.2 rule 1: `<`, `>`, `<=`, `>=`, `=` and `<>` are refused "**as operators of
`expr`** — they appear only inside a `cond` (rule 10), which is the whole of
their grammar." And rule 10: "A `comparison` is **not** an expression and has no
value."

The reason is the format's value model, not taste: "`a < b` is not a column
formula, because there is no value for it to have: the format has numbers and
errors and no boolean, and rule 10 exists precisely so that adding `if` did not
have to add a third kind of value."

Rule 10's [CHOICE] spells out what accepting this would cost: "a boolean is
storable, so `| flag = q > 0 |` becomes a column whose data cells hold something
§4.1.6 has no spelling for, and §10 could not canonicalise it, and `sum` over it
would need a meaning."

An implementation that gives `comparison` a value — the natural design, since
`if` needs one — accepts this file and has to render `flag`. Whatever it renders
(`1`, `true`, `TRUE`) is a value §4.1.6 does not define and §10 cannot round
trip, and `n := count(flag)` will report `1` for it.
