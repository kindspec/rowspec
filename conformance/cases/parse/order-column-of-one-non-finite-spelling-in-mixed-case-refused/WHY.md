# Why this case exists

The order column `o` holds `INFINITY`, `iNfInItY` and `InFiNiTy`: one
spelling in three cases, none of them lower case, and nothing else. A key is
declared and `o` is stored.

§4.1.6: "Refused, and therefore text — ... and `inf`, `nan` and `infinity` in
any case." So none of these cells is a number, and the column is text in every
row.

§9.10 (`bad-order-column`) refuses "`order := by(c)` where `c` is not a stored
column, is computed, mixes types, **is blank in any row**, or holds a
non-finite spelling (`inf`, `nan`, `infinity`, any case, bare or after one
leading `+` or `-`) in any row (§6)". §6: "Non-finite numbers in `c` are
refused, and so is a non-finite **spelling** (§9.10)".

The refusal is on the spelling, not on the column's type. §9.10 says "any
case", so an upper- or mixed-case spelling is refused as the lower-case one
is. No cell is lower case, so a reader that matches the spellings
case-sensitively finds none and accepts the file. The three cells are distinct
text, so the column has a total order and nothing about types refuses it.
