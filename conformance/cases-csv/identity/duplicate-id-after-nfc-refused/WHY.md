Key values `café` (U+00E9) and `cafe` + U+0301 are equal after NFC (§3), so
with `id` declared as the key they are a duplicate row id (§9.5). Each is a
valid `ident`.

## Identifier

This case asserts `refusal: "duplicate-row-id"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "two rows with one value of the declared key: §9.5 `duplicate-row-id`."

§9.5: "`duplicate-row-id`: a duplicate row id, where a key is declared"
