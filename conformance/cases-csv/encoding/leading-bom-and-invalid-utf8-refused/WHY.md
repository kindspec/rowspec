The file starts with a BOM and later holds the lone byte `0xE9`. The BOM is a warning; the byte is not.

## Identifier

This case asserts `refusal: "bad-encoding"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "refusals 26 (`leading-bom`) and 15 (`lone-cr`) are warnings in CSV mode; 14 (`bad-encoding`) is still refused."

§13: "a CSV that is not well-formed UTF-8: §9.14 `bad-encoding`."

§13: "A warning, §9.26's and §9.15's included, is not a refusal, and is not checked against the case's identifiers."

§9.14: "`bad-encoding`: bytes that are not well-formed UTF-8 (§3). A property of the bytes, decided before any line is classified."
