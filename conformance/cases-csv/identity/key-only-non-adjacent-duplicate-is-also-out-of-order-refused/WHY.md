`r1` is held by the first and third rows, with `r2` between them, so the file meets §9.5. The adjacent pair `r2`, `r1` is also out of key order.

## Identifier

This case asserts `refusal: "duplicate-row-id"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "two rows with one value of the declared key: §9.5 `duplicate-row-id`."

§9.28: "It is the exception to the rule below that any applicable refusal may be reported: a file that any other entry refuses is reported under that entry, since only this entry is repairable by `canon`, and two rows holding one key are always §9.5".

The rows are also out of order, and §9.28 yields to the other entry, so `rows-out-of-order` is not listed and a reader that reports it fails this case.
