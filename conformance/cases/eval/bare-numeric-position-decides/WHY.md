# Why this case exists

§4.2 rule 7: "**A bare numeric token: the position decides.**" Name positions
"admit `ident` and have **no literal alternative**. `sum(123)` is the column
named `123`." Operand position "tries `literal` first, so a token matching
`literal` is a number. `| c = 123 * 2 |` is `246`."

This fixture puts both positions in one file **with a column named `123`
actually present**, which is the only arrangement that can tell the rule from
the alternative the spec rejects — "resolve a bare numeric token to the column
if such a column exists, and to a literal otherwise". Under that alternative
`c` would be 14, not 246. Under the rule the same token is a number in one cell
and a column name in the next.
