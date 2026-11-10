The first two data rows are out of key order. The last record has one field under a header of two.

## Identifier

This case asserts `refusal: "row-field-count"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a record whose field count differs from the header's, an empty line between rows included, a quoted field the file ends inside, and a stray quote: §9.6 `row-field-count`."

§9.28: "It is the exception to the rule below that any applicable refusal may be reported: a file that any other entry refuses is reported under that entry, since only this entry is repairable by `canon`, and two rows holding one key are always §9.5".

The rows are also out of order, and §9.28 yields to the other entry, so `rows-out-of-order` is not listed and a reader that reports it fails this case.
