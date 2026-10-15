# Why this case exists

The second key value is `r_02` with a trailing U+3000 IDEOGRAPHIC SPACE.

§4: "**Cell values are trimmed of leading and trailing ASCII space and
horizontal tab, and of nothing else.**" §4.1.4: "A cell's value is its
text with leading and trailing `WSP` removed, and nothing else removed",
with §4.1's "`WSP = SP / HTAB` — ASCII space U+0020 and horizontal tab
U+0009, never the Unicode `White_Space` property".

The character is not `WSP`, so it is part of the key value.

§4.1.9: column names, aggregate names, the argument of `key` and `order`,
and the values of the key column "are `ident`: one or more Unicode
letters, marks or digits, or `_`. Whitespace and `Cf` are excluded by
construction". §9.16 (`bad-identifier`) refuses "an identifier — column
name, aggregate name, `key`/`order` argument, or a value of the key
column — containing whitespace, a `Cf` format character, or any character
outside `ident`".

It is not a letter, mark, digit or `_`, so the key value is refused under
§9.16. The neighbour `parse/key-values-differing-by-tab-padding-are-duplicates-refused`
pads with a tab, which is trimmed.
