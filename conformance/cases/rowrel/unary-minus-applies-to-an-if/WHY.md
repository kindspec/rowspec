# Why this case exists

`factor = [ "-" *WSP ] primary` and `cond` is a `primary`, so `-if(...)` is a
`factor` and is well-formed. §4.2 rule 1: "Unary `-` binds tighter than any
binary operator".

Included because a parser that reaches `if` through a special case in `primary`
often reaches it *instead of* `factor` — dispatching on the leading token before
the optional sign is consumed — and then refuses this cell. §4.2's whole-cell
recognition rule makes that refusal, not a fallback, but the file is valid and
the answer is `-2`.

Rule 7's "A `factor` carries at most one unary minus" still holds around a
`cond`: `--if(...)` is not generated.
