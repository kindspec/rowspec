# Why this case exists

§4.2 rule 7: "**`sum(1)` is `#REF!(1)`** — a broken reference to a column named
`1`, under §8's ordinary rule for a name that does not exist."

The spec explains why it is not a refusal, and the explanation is what makes
this worth pinning: "refusing this one would mean refusing an aggregate over any
absent column — which contradicts the fixtures that pin `#REF!` as the answer,
and would make a formula's *acceptance* depend on the header rather than on its
own bytes."
