# Why this case exists

§4.2 rule 1: "Precedence, tightest first: parentheses; unary `-`; `*` and `/`;
`+` and `-`. Binary operators are **left-associative**, so `8 - 4 - 2` is `2`
and `8 / 4 / 2` is `1`. Unary `-` binds tighter than any binary operator, so
`-a + b` is `(-a) + b`."

Every clause of that sentence is one column here. Right-associativity would make
`d` 4.0; giving unary `-` the lower precedence would make `u` -13.0.
