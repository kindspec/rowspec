# Why this case exists

The order column `o` holds `inf`, `NaN` and `Infinity`, one per row, and nothing else. A key is declared and `o` is stored.

§4.1.6: "Refused, and therefore text — ... and `inf`, `nan` and `infinity` in
any case." So none of these cells is a number, and the column is text in every row.

§9.10 (`bad-order-column`) refuses "`order := by(c)` where `c` is not a stored
column, is computed, mixes types, **is blank in any row**, or holds a
non-finite spelling (`inf`, `nan`, `infinity`, any case) in any row (§6)". §6:
"Non-finite numbers in `c` are refused."

The refusal is on the spelling, not on the column's type. Read by type alone, a column of only these spellings is a single-type `text` column with a total order by code point (§4.1.8), and nothing about types refuses it. §9.10 says "holds a non-finite spelling ... in any row", and every row here does. A reader that checks for these spellings only among numbers, or only when a number sits beside them, accepts this file.
