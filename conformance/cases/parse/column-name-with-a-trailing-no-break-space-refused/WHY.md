# Why this case exists

The second column's name is `qty` with a trailing U+00A0 NO-BREAK SPACE.

§4: "**Cell values are trimmed of leading and trailing ASCII space and
horizontal tab, and of nothing else.**" §4.1.4: "A cell's value is its
text with leading and trailing `WSP` removed, and nothing else removed",
with §4.1's "`WSP = SP / HTAB` — ASCII space U+0020 and horizontal tab
U+0009, never the Unicode `White_Space` property".

The character is not `WSP`, so it is part of the name.

§4.1.9: column names, aggregate names, the argument of `key` and `order`,
and the values of the key column "are `ident`: one or more Unicode
letters, marks or digits, or `_`. Whitespace and `Cf` are excluded by
construction". §9.16 (`bad-identifier`) refuses "an identifier — column
name, aggregate name, `key`/`order` argument, or a value of the key
column — containing whitespace, a `Cf` format character, or any character
outside `ident`". §4: "Whitespace is also **rejected in identifiers** — column
names, aggregate names and row keys".

No aggregate names the column, so §9.16 is the one refusal that applies.
