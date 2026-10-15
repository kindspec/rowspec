# Why this case exists

The control for `parse/declaration-argument-with-a-*-refused`: the argument
of `sum` is `qty` padded with ASCII spaces and horizontal tabs.

§4.1: `rhs = ident "(" *WSP arg *WSP ")"`, with `WSP = SP / HTAB`. The
padding is the two `*WSP`, so the line is a declaration, the argument is
`qty`, and `g` is `5`.
