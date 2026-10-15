# Why this case exists

The third header cell is `t`, a U+3000 IDEOGRAPHIC SPACE, then `= a * 2`.

§5: "**The split is at the cell's first `=`.**" The name is what precedes
it. §4: "**Cell values are trimmed of leading and trailing ASCII space and
horizontal tab, and of nothing else.**" §4.1.4: "A cell's value is its
text with leading and trailing `WSP` removed, and nothing else removed",
with §4.1's "`WSP = SP / HTAB` — ASCII space U+0020 and horizontal tab
U+0009, never the Unicode `White_Space` property".

U+3000 is not `WSP`, so the name is `t<U+3000>`.

§4.1.9: column names, aggregate names, the argument of `key` and `order`,
and the values of the key column "are `ident`: one or more Unicode
letters, marks or digits, or `_`. Whitespace and `Cf` are excluded by
construction". §9.16 (`bad-identifier`) refuses "an identifier — column
name, aggregate name, `key`/`order` argument, or a value of the key
column — containing whitespace, a `Cf` format character, or any character
outside `ident`".

The formula `a * 2` is well-formed, so §9.16 is the one refusal that
applies.
