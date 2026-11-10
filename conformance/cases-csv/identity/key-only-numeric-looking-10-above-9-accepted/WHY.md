Keys that look like numbers: `10` above `9`.

§13: "Where the sidecar declares `key` and no `order`, the rows MUST be in ascending order of the key's value as §4.1.8 orders text, or the file is refused (§9.28)."

A key is compared as text. `1` (U+0031) precedes `9` (U+0039), and §13 gives a key no numeric reading.

The twin `identity/key-only-numeric-looking-9-above-10-refused` holds the keys the other way up and is refused.
