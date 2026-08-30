# Why this case exists

§4.2 rule 10 prints this exact shape as well-formed: "`if(q > 0, if(r > 0, 1, 2),
3)`". A branch is an `expr`, `expr` reaches `primary`, and `primary` includes
`cond`, so nesting needs no separate rule.

`r_01` takes the outer *then* branch and the inner *else* branch, so the answer
is `2` — the value reachable only by getting both nestings right. `1` means the
inner comparison was misread, `3` means the outer one was.

Laziness compounds here: the outer `else` (`3`) is never evaluated in `r_01`,
and in `r_02` neither arm of the inner `if` is, because the inner `if` itself is
not evaluated. An implementation that evaluates eagerly still gets the right
number in this file — which is why the laziness cases are separate and use
errors rather than values.
