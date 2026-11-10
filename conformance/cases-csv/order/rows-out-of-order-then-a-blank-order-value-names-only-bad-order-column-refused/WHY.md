The first two data rows are out of order by `o`. The last row's `o` is blank, which §13 refuses.

## Identifier

This case asserts `refusal: "bad-order-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "an `order` naming no column of the file, and an order column that mixes types, is blank in any row, or holds a non-finite value: §9.10 `bad-order-column`, whose "`c` is not a stored column" is the first."

§9.28: "It is the exception to the rule below that any applicable refusal may be reported: a file that any other entry refuses is reported under that entry, since only this entry is repairable by `canon`, and two rows holding one key are always §9.5".

The rows are also out of order, and §9.28 yields to the other entry, so `rows-out-of-order` is not listed and a reader that reports it fails this case.
