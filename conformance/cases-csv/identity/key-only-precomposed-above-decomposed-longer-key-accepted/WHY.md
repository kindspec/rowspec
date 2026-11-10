A key of U+00E9 and a key of U+0065 U+0301 U+0062, whose NFC form is U+00E9 U+0062: `é` above `éb`.

§13: "Where the sidecar declares `key` and no `order`, the rows MUST be in ascending order of the key's value as §4.1.8 orders text, or the file is refused (§9.28)."

§4.1.8 compares the NFC-normalised value, so `é` is a proper prefix of the longer key and sorts first. On raw code points U+0065 is below U+00E9, which gives the opposite answer.

The twin `identity/key-only-decomposed-longer-key-above-precomposed-refused` holds the keys the other way up and is refused.
