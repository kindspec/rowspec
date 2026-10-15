# Why this case exists

The last declaration ends with a U+000B VERTICAL TAB.

§4.1: `declaration = *WSP ident *WSP ":=" *WSP rhs [ 1*WSP "#" *char ] *WSP eol`,
and `WSP` is ASCII space and horizontal tab only. A vertical tab is not
`WSP`, so the line does not match `declaration`.

§9.12 (`malformed-declaration`): "a line containing `:=` that does not match
`declaration`". The neighbour `eval/tab-after-a-declaration-is-whitespace`
ends the same line with a horizontal tab.
