# Why this case exists

The order column `n` holds `10` and `9` padded with horizontal tabs.

§4: "**Cell values are trimmed of leading and trailing ASCII space and
horizontal tab, and of nothing else.**" §4.1.4: "A cell's value is its
text with leading and trailing `WSP` removed, and nothing else removed",
with §4.1's "`WSP = SP / HTAB` — ASCII space U+0020 and horizontal tab
U+0009, never the Unicode `White_Space` property".

The padded cell trims to `9`, a `number`, so the column is numeric
throughout. §6: `c` "must have a single type across all rows — `number`, `date`
(`Y-M-D` or `Y/M/D`), or `text`. **Mixed types are refused**", and §9.10
(`bad-order-column`) refuses an order column that "mixes types". No type is mixed, a key is declared, and the file is
accepted. A reader that does not trim the tab reads text beside a number
and refuses it.
