Byte 0xE9 followed by LF is not well-formed UTF-8 (it is Latin-1 `é`).
§9.14 covers both a leading BOM and bytes that are not well-formed UTF-8;
§13 demotes refusal 14 to a warning, labelling it "(BOM)". Reading: only
the BOM half is demoted. §13's stated reason is about BOMs, and decoding
invalid bytes means substituting characters, which can change values and
make distinct identifiers equal.
