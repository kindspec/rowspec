# Why this case exists

SPEC.md §4.1.7: "A cell is a date only if it matches `date`; **the two
separators within one date must be the same character.** [CHOICE] --
`2024-01/05` is a typo, and a format that accepts it accepts a value nobody
wrote."

So `2024-01/05` is not a date. §4.1.6's rule then applies -- a cell that does
not match its literal grammar is text -- and the column holds one date and one
text value. §6: "**Mixed types are refused**, because they have no total order",
and §9.10 lists it.

`rowspec.table` ACCEPTS this file and orders it; `rowspec_alt.table` refuses it
as mixed. I judge the reference at fault: §4.1.7 states the same-separator rule
and gives its reason in the same sentence.
