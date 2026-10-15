# Why this case exists

The order column `o` holds `apple`, `+nan`: `nan` after one leading `+`, and
`pear`. A key is declared and `o` is stored.

§4.1.6: "Refused, and therefore text — ... and `inf`, `nan` and `infinity`
in any case." The grammar's `number` is `[ "-" ] 1*DIGIT [ "." 1*DIGIT ]`,
so a sign does not make any of them a number.

So every cell is text and the column does not mix types.

§6: "Non-finite numbers in `c` are refused, and so is a non-finite
**spelling** (§9.10): `inf`, `nan` or `infinity` in any case, bare or after
one leading `+` or `-`. Each is text under §4.1.6, signed or not, but
Python's `float()` reads every one of them as a number, so a host that reads
the column would sort it differently from rowspec."

§9.10 (`bad-order-column`) refuses "`order := by(c)` where `c` is not a
stored column, is computed, mixes types, **is blank in any row**, or holds a
non-finite spelling (`inf`, `nan`, `infinity`, any case, bare or after one
leading `+` or `-`) in any row (§6)".

One row holds a signed non-finite spelling, and one is enough: "in any row".
A reader that checks the spellings only while reading a column as numbers
never looks at a text column, and a reader that matches only the bare
spellings never matches this cell; either accepts this file.
