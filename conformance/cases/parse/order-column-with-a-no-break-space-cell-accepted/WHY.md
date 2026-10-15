# Why this case exists

The order column `o` holds a single U+00A0 NO-BREAK SPACE, `b` and `c`.
§4.1.4: a cell's value is its text with `WSP` removed "and nothing else
removed", and §4.1's `WSP` is ASCII space and tab only. So the U+00A0
cell is text, not blank, and the column is a `text` column throughout.

§9.10 (`bad-order-column`) refuses an order column that "mixes types, **is
blank in any row**, or holds a non-finite spelling". None applies, a key
is declared, and the file is accepted. A reader that trims U+00A0 sees a
blank and refuses.
