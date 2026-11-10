An ASCII key and a precomposed non-ASCII key: `z` above `é`.

§13: "Where the sidecar declares `key` and no `order`, the rows MUST be in ascending order of the key's value as §4.1.8 orders text, or the file is refused (§9.28)."

`z` is U+007A and `é` is U+00E9. Locale collation would put `é` before `z`.

The twin `identity/key-only-non-ascii-above-ascii-refused` holds the keys the other way up and is refused.
