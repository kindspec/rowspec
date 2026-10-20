An empty line inside the data. Under RFC 4180's grammar it is a record of
one empty field (a reader that yields zero fields gets a mismatch too), and
the header has two, so §9.6 applies. Reading: CSV has no blank-line
channel; .mdtbl's blank line exists only outside the table (§4.1.2), and
skipping it silently would make the record count depend on the reader.

## Identifier

This case asserts `refusal: "row-field-count"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a record whose field count differs from the header's, an empty line between rows included, a quoted field the file ends inside, and a stray quote: §9.6 `row-field-count`."

§9.6: "`row-field-count`: a data row whose field count differs from the header"
