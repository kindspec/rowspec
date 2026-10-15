# Why this case exists

The control for the declaration cases of this batch
(`parse/declaration-*-empty-argument-refused`,
`parse/declaration-sum-argument-with-a-*-refused`). Each refused case puts
something other than an `ident` between a function's parentheses; this one
puts an `ident` there, with `_` where those had `-` or `.`.

§4.1.9: `ident` admits "one or more Unicode letters, marks or digits, or
`_`". So `a_b` and `n_x` are column names and declaration arguments, and every
line here matches `declaration`.

Values, from §7: `t := sum(a_b)` is 5 + 7 + 11 = `23`; `u := sum(n_x)` is
1 + 2 + 4 = `7`; `v := sum(a_b where k = "x")` matches rows `r_01` and `r_03`,
5 + 11 = `16`; `w := count(a_b)` counts three rows.

Without it, a reader that refused every declaration would pass the refused
cases.
