# Why this case exists

Sibling of `order-column-blank-in-every-row-refused`, with a row-relative
column that depends on the order: `run = cumulative(amt)`, ordered by a
column `d` that is blank in every row.

§9.10 refuses the order column because it "is blank in any row", and §6
gives the reason: the order "is what every row-relative value is computed
over, so a spelling that has no defined place in it would put a running
total's meaning in the hands of whichever reader guessed". Here that is
concrete: if the file were accepted, `run` would be 5 then 12 or 7 then 12
depending on which row the reader put first, and the tie-break on `key`
would quietly decide it.

The order is declared, so §9.9 does not apply; a key is declared, so §9.25
does not apply. `bad-order-column` is the one refusal.
