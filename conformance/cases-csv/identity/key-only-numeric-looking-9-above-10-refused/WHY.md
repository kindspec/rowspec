Keys that look like numbers: `9` above `10`.

§13: "Where the sidecar declares `key` and no `order`, the rows MUST be in ascending order of the key's value as §4.1.8 orders text, or the file is refused (§9.28)."

A key is compared as text. `1` (U+0031) precedes `9` (U+0039), and §13 gives a key no numeric reading.

The twin `identity/key-only-numeric-looking-10-above-9-accepted` is accepted.

## Identifier

This case asserts `refusal: "rows-out-of-order"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "rows that do not follow the declared `order`, or the `key` where no `order` is declared: §9.28 `rows-out-of-order`."

§9.28: "`rows-out-of-order`: a table that declares a key, and a row whose key does not sort after the key of the row above it, as §4.1.8 orders text (§6). In §13's CSV profile, rows that do not follow the sidecar's `order`, or its `key` where it declares no `order` (§13)"
