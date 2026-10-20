The sidecar is `{"key": "id"}` in UTF-16 big-endian with a byte-order mark; `0xFE` never occurs in UTF-8.

## Identifier

This case asserts `refusal: "bad-encoding"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a sidecar whose bytes are not well-formed UTF-8: §9.14 `bad-encoding`, which is a property of bytes in whichever file holds them."

§13: "A sidecar encoded as UTF-16 or UTF-32 meets whichever rule its bytes meet: with a byte-order mark its bytes are not well-formed UTF-8, so it is `bad-encoding`; without one, a sidecar of ASCII characters only is well-formed UTF-8 that is not valid JSON, so it is `malformed-declaration` as above."

§9.14: "`bad-encoding`: bytes that are not well-formed UTF-8 (§3). A property of the bytes, decided before any line is classified."
