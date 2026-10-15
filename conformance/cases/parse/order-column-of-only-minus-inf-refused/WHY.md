# Why this case exists

The order column `o` holds `-inf`: `inf` after one leading `-`, in both
rows, and nothing else. A key is declared and `o` is stored.

§4.1.6: "Refused, and therefore text — ... and `inf`, `nan` and `infinity`
in any case." The grammar's `number` is `[ "-" ] 1*DIGIT [ "." 1*DIGIT ]`,
so a sign does not make any of them a number.

So both cells are text and the column is a single-type `text` column; ties
fall to the key (§6). Nothing about types refuses it.

§6: "Non-finite numbers in `c` are refused, and so is a non-finite
**spelling** (§9.10): `inf`, `nan` or `infinity` in any case, bare or after
one leading `+` or `-`. Each is text under §4.1.6, signed or not, but
Python's `float()` reads every one of them as a number, so a host that reads
the column would sort it differently from rowspec."

§9.10 (`bad-order-column`) refuses "`order := by(c)` where `c` is not a
stored column, is computed, mixes types, **is blank in any row**, or holds a
non-finite spelling (`inf`, `nan`, `infinity`, any case, bare or after one
leading `+` or `-`) in any row (§6)".

Every row holds a signed non-finite spelling, so §9.10 applies. A reader
that matches only the bare spellings, or that hands the cell to a host float
parser and treats a parsed infinity or NaN as a number it may sort, accepts
this file.
