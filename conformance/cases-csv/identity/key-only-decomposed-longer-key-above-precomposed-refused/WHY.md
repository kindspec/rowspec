A key of U+00E9 and a key of U+0065 U+0301 U+0062, whose NFC form is U+00E9 U+0062: `éb` above `é`.

§13: "Where the sidecar declares `key` and no `order`, the rows MUST be in ascending order of the key's value as §4.1.8 orders text, or the file is refused (§9.28)."

§4.1.8 compares the NFC-normalised value, so `é` is a proper prefix of the longer key and sorts first. On raw code points U+0065 is below U+00E9, which gives the opposite answer.

The twin `identity/key-only-precomposed-above-decomposed-longer-key-accepted` is accepted.

## Identifier

This case asserts `refusal: "rows-out-of-order"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "rows that do not follow the declared `order`, or the `key` where no `order` is declared: §9.28 `rows-out-of-order`."

§9.28: "`rows-out-of-order`: a table that declares a key, and a row whose key does not sort after the key of the row above it, as §4.1.8 orders text (§6). In §13's CSV profile, rows that do not follow the sidecar's `order`, or its `key` where it declares no `order` (§13)"
