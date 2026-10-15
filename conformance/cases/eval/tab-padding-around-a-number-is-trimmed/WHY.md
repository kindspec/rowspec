# Why this case exists

The two `qty` cells are `5` and `7` padded with horizontal tabs and spaces.

§4: "**Cell values are trimmed of leading and trailing ASCII space and
horizontal tab, and of nothing else.**" §4.1.4: "A cell's value is its
text with leading and trailing `WSP` removed, and nothing else removed",
with §4.1's "`WSP = SP / HTAB` — ASCII space U+0020 and horizontal tab
U+0009, never the Unicode `White_Space` property".

Both cells trim to a `number`, so `g` is `12`. The neighbours
`eval/em-space-padding-is-not-trimmed` and
`eval/ideographic-space-padding-is-not-trimmed` pad with characters that are
not `WSP`.
