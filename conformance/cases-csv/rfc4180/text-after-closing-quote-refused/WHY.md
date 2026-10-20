Anything but the delimiter or a line break after a closing quote is
a stray quote, refused as the profile's reading of §9.6 (SPEC.md §13,
RFC 4180 §2). Issue #94 item 9.

## Identifier

This case asserts `refusal: "row-field-count"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a record whose field count differs from the header's, an empty line between rows included, a quoted field the file ends inside, and a stray quote: §9.6 `row-field-count`."

§9.6: "`row-field-count`: a data row whose field count differs from the header"
