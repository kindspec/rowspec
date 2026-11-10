A key of U+FF21 and a key of U+1D400: `Ａ` above `𝐀`.

§13: "Where the sidecar declares `key` and no `order`, the rows MUST be in ascending order of the key's value as §4.1.8 orders text, or the file is refused (§9.28)."

The comparison is by code point. A comparison of UTF-16 code units would put U+1D400 first.

The twin `identity/key-only-astral-above-fullwidth-refused` holds the keys the other way up and is refused.
