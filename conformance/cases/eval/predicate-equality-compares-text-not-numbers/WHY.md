# Why this case exists

§4.2 rule 6: "**Equality compares text, never numbers.** ... So `where qty = "3"`
matches a cell holding `3` and not one holding `3.0`."

That is this fixture, with the spec's own two spellings. If the comparison
coerced, both rows would match and `hi` would be 110.0 — which is what
`rowspec_alt` returns.

The reason travels with the rule: "a second spelling that compares equal as a
number and unequal as text splits `where` predicates from key identity. A
predicate is grouping, and grouping is identity."
