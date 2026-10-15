# Why this case exists

The key values are `r_01` and `r_01` padded with horizontal tabs.

§4.1.4: "Trimming is also what makes text comparison total: a row keyed
`r_01` and a row keyed `<tab>r_01` must be one duplicate (§9.5), not two rows
that render identically."

§4: "**Cell values are trimmed of leading and trailing ASCII space and
horizontal tab, and of nothing else.**" §4.1.4: "A cell's value is its
text with leading and trailing `WSP` removed, and nothing else removed",
with §4.1's "`WSP = SP / HTAB` — ASCII space U+0020 and horizontal tab
U+0009, never the Unicode `White_Space` property".

Both trim to `r_01`, a valid `ident`, so §9.5 (`duplicate-row-id`) is the
one refusal that applies.
