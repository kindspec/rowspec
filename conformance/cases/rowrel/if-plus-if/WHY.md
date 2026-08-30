# Why these cases exist

§4.2 rule 10: "**`if` is a `primary`, and a comparison exists nowhere else.**
`if(c, a, b)` is an operand like any other, so it composes — `if(q > 0, t, 0) * 2`
and `if(q > 0, if(r > 0, 1, 2), 3)` are well-formed".

The hazard is rule 3, which says the opposite about the *other* two shapes: "**A
call is the whole formula or nothing.** `cumulative(a) * 2`,
`sum(a where b = "x") + 1` and `prior(a) - a` are refused. A `call` never
appears as a `primary`". An implementer who has just implemented rule 3 — and
whose parser therefore has a "function call at top level only" gate — will
generalise it to `if`, because `if(...)` looks exactly like the calls that gate
was built for. It is not one: `cond` is listed in `primary` and `rowrel-call`
and `group-call` are not.

`parse/if-composed-into-arithmetic-accepted` is the refusal-side twin, and
`parse/aggregate-call-inside-an-if-branch-refused` is the same boundary from
the other direction — a `call` still does not compose, even inside a branch.
