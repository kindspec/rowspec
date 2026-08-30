# Why this case exists

§4.2 rule 10 names only one spelling of the blank test — "`if(x = "", a, b)`
is the blank test" — but `=` and `<>` are given one rule between them: "`=` and
`<>` compare **text or numbers, and the right-hand side's spelling decides
which**." `""` is a `string`, so `q <> ""` is a text comparison, a blank cell's
text is the empty string, and the answer is false.

`if(x <> "", a, b)` is the *present*-value test, and it is at least as common in
real sheets as the missing-value one — it is how a column gets "use it if it's
there". An implementation that hard-codes the exception on the literal token
sequence `= ""` — which is the cheapest way to satisfy
`rowrel/if-blank-test-is-true-for-a-blank-cell` — falls through to the loud path
here and returns `#REF!(q)`.

Row `r_01` holds `5`, whose text is not empty, so the same formula is `1` there:
the case cannot be passed by returning `0` unconditionally.
