# Why this case exists

The order column `n` holds `10` and `9` with a U+00A0 NO-BREAK SPACE on each side.

§4: "**Cell values are trimmed of leading and trailing ASCII space and
horizontal tab, and of nothing else.**" §4.1.4: "A cell's value is its
text with leading and trailing `WSP` removed, and nothing else removed",
with §4.1's "`WSP = SP / HTAB` — ASCII space U+0020 and horizontal tab
U+0009, never the Unicode `White_Space` property".

U+00A0 NO-BREAK SPACE is not `WSP`, so the second value is `<U+00A0 NO-BREAK SPACE>9<U+00A0 NO-BREAK SPACE>`, which
does not match `number` (§4.1.6) or `date` (§4.1.7) and is text.

§6: `c` "must have a single type across all rows — `number`, `date`
(`Y-M-D` or `Y/M/D`), or `text`. **Mixed types are refused**", and §9.10
(`bad-order-column`) refuses an order column that "mixes types".

The column holds a number and a text value, so it is refused. The existing `parse/order-column-with-a-no-break-space-cell-accepted`
holds a U+00A0 cell beside text, which is all text. The neighbour
`parse/order-column-tab-padded-number-accepted` pads with a tab, which is
trimmed.
