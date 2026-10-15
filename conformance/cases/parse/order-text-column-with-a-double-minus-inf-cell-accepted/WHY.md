# Why this case exists

The control for `parse/order-text-column-with-one-*-cell-refused` and the
signed cases beside them. The order column `o` holds `apple`, `--inf` and
`pear`. A key is declared and `o` is stored.

`--inf` carries two leading signs, and §6 admits "one leading `+` or `-`".

§9.10 (`bad-order-column`) refuses a column that "holds a non-finite
spelling (`inf`, `nan`, `infinity`, any case, bare or after one leading `+`
or `-`) in any row". `--inf` is not one of those spellings, bare or signed.
Every cell is text under §4.1.6, so the column is `text` in every row, never
blank, stored, and a key is declared. The file is accepted.

A reader that refuses on a substring match, or that strips every sign or
space before matching, refuses this file.
