# Why this case exists

The header cell of the second column is `qty` padded with horizontal tabs.

§4: "**Cell values are trimmed of leading and trailing ASCII space and
horizontal tab, and of nothing else.**" §4.1.4: "A cell's value is its
text with leading and trailing `WSP` removed, and nothing else removed",
with §4.1's "`WSP = SP / HTAB` — ASCII space U+0020 and horizontal tab
U+0009, never the Unicode `White_Space` property". A header cell is a cell of the table's first line (§4), and §5:
"A header cell is a NAME, or a name and a formula separated by `=`".

The name trims to `qty`, so `sum(qty)` resolves and `g` is `5`.
