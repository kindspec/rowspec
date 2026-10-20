The sidecar is `{"key": "café"}` in UTF-16 little-endian with no byte-order mark. `é` is the bytes `0xE9 0x00`, and `0xE9` opens a three-byte UTF-8 sequence that `0x00` cannot continue.

## Identifier

This case asserts `refusal: "bad-encoding"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a sidecar whose bytes are not well-formed UTF-8: §9.14 `bad-encoding`, which is a property of bytes in whichever file holds them."

§13: "A sidecar encoded as UTF-16 or UTF-32 meets whichever rule its bytes meet: with a byte-order mark its bytes are not well-formed UTF-8, so it is `bad-encoding`; without one, a sidecar of ASCII characters only is well-formed UTF-8 that is not valid JSON, so it is `malformed-declaration` as above."

§9.14: "`bad-encoding`: bytes that are not well-formed UTF-8 (§3). A property of the bytes, decided before any line is classified."

§13 settles the ASCII-only sidecar without a byte-order mark; this one is not ASCII-only, so it "meets whichever rule its bytes meet", and its bytes are not well-formed UTF-8. As in `sidecar/non-utf8-byte-in-a-name-refused`, they are never read as JSON.
