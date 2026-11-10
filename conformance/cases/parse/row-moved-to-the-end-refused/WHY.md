# Why this case exists

`r_03` sits after `r_06`, the shape a branch has when it moves a row to the end of the table.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

§6: "Requiring key order refuses the moved row on the branch that moved it, and again after the merge".

This file is the moving side of `merge/row-moved-to-the-end-on-ours-deleted-on-theirs-refused`. The `merge` kind asserts on the merged file alone, so this case pins the refusal of that side.

Nothing else in the file is refused, so `rows-out-of-order` is the only identifier §9 allows.
