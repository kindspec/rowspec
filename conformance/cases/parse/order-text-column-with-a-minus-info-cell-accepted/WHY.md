# Why this case exists

The control for `parse/order-text-column-with-one-*-cell-refused` and the
signed cases beside them. The order column `o` holds `apple`, `-info` and
`pear`. A key is declared and `o` is stored.

`-info` is a sign before `info`, which is none of `inf`, `nan` or
`infinity`.

§9.10 (`bad-order-column`) refuses a column that "holds a non-finite
spelling (`inf`, `nan`, `infinity`, any case, bare or after one leading `+`
or `-`) in any row". `-info` is not one of those spellings, bare or signed.
Every cell is text under §4.1.6, so the column is `text` in every row, never
blank, stored, and a key is declared. The file is accepted.

A reader that refuses on a substring match, or that strips every sign or
space before matching, refuses this file.
