# Why this case exists

The accepted neighbour of the `parse/order-column-*-mixes-types-refused`
cases: every value of the order column `n` is a spelling §4.1.6 refuses as a
number — `5.`, `٥` (U+0665), `+5` and `.5` — so every value is text and the
column is a `text` column with no mixing (§6).

§4.1.8: "A `text` order column (§6) … compare[s] by **Unicode code point**
over the NFC-normalised, trimmed value." By first code point the order is
`+5` (U+002B), `.5` (U+002E), `5.` (U+0035), `٥` (U+0665), so
`run` in the second row is `1 + 10`, `11`.

A reader that reads any of these as the number it resembles either refuses
the file as mixed or puts `.5` first, and gives `110`.
