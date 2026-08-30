# Why this case exists

§4.2 rule 10: "**A branch that is not a number is refused, and it is refused by
the grammar rather than by a rule.** `expr` does not generate `string`, so
`if(c = "x", "PASS", "FAIL")` is not a `formula` and the header cell is
refused under §9.20."

Rule 10 measures this one: "**5,943 corpus cells, 47% of every `if` in the
corpus, and the single largest thing this rule does not do.**" It is therefore
the shape an implementer is most likely to accommodate — the users will ask for
it, `string` is already in the grammar for predicates, and the parser is already
parsing one three tokens earlier on the same line.

Accepting it is not a grammar relaxation: "Admitting it is not a grammar change
but a *value-model* change: a computed column that can hold text changes what
`sum` over that column means, what a `where` predicate compares against, what
§10 canonicalises and what §9.17 checks."

The aggregate is `count` rather than `sum` so that, if the refusal does not
fire, what surfaces is not additionally an aggregate-coercion error — §7's
`count` "counts rows and never coerces", so a reader that accepted text branches
would report `1` here and look entirely healthy.
