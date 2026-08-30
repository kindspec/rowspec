# Why this case exists

§9.16 refuses "an identifier — column name, aggregate name, `key`/`order`
argument, or a value of the key column — containing whitespace, a `Cf` format
character, or any character outside `ident`", and §4.1.9's ABNF is
`ident = 1*( LETTER / MARK / NUM / "_" )`, which excludes `|`.

The escape makes a pipe *writable in a cell*; it does not make it legal in an
*identifier*. The two rules are independent and the interaction is new, so it
needs saying: `r\|01` is a well-formed cell holding `r|01`, and `r|01` is not a
well-formed row key.

Left as `refusal_contains: ""` deliberately — §9.16 and §9.5-adjacent
diagnostics could both reasonably fire, and §9 says which one is reported is
unspecified.
