# Why this case exists

The control for `parse/order-*-non-finite-*-refused` and
`parse/order-text-column-with-one-*-cell-refused`. The order column `o` holds
`info`, `nano` and `infinite`, each of which begins with one of §9.10's
spellings and none of which is one.

§9.10 (`bad-order-column`) refuses a column that "holds a non-finite spelling
(`inf`, `nan`, `infinity`, any case, bare or after one leading `+` or `-`)
in any row". A spelling is the whole
trimmed cell, as §4.1.6 reads a cell as a number "only if it matches
`number`". These three cells are ordinary text: the column is `text` in
every row, never blank, stored, and a key is declared. The file is accepted.

A reader that refuses on a prefix or substring match refuses this file.
