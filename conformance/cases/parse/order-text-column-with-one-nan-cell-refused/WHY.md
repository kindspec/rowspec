# Why this case exists

The order column `o` holds `apple`, `nAn` and `pear`. A key is declared and `o` is stored.

§4.1.6: "Refused, and therefore text — ... and `inf`, `nan` and `infinity` in
any case." So none of these cells is a number, and the column is text in every row.

§9.10 (`bad-order-column`) refuses "`order := by(c)` where `c` is not a stored
column, is computed, mixes types, **is blank in any row**, or holds a
non-finite spelling (`inf`, `nan`, `infinity`, any case, bare or after one
leading `+` or `-`) in any row (§6)". §6: "Non-finite numbers in `c` are
refused, and so is a non-finite **spelling** (§9.10)".

The refusal is on the spelling, not on the column's type. `apple` and `pear` are ordinary text, so the column does not mix types. `nAn` is one of §9.10's spellings in some case, and one such row is enough: "in any row". A reader that checks for the spellings only while reading a column as numbers never looks at a text column and accepts this file.
