Byte 0xE9 followed by LF is not well-formed UTF-8 (it is Latin-1 `é`).
§9.14 covers both a leading BOM and bytes that are not well-formed UTF-8;
§13 demotes refusal 14 to a warning, labelling it "(BOM)". Reading: only
the BOM half is demoted. §13's stated reason is about BOMs, and decoding
invalid bytes means substituting characters, which can change values and
make distinct identifiers equal.

## Identifier

This case asserts `refusal: "bad-encoding"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a CSV that is not well-formed UTF-8: §9.14 `bad-encoding`."

§9.14: "`bad-encoding`: bytes that are not well-formed UTF-8 (§3). A property of the bytes, decided before any line is classified."
