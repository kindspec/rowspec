# Why this case exists

An upper-case and a lower-case key: `B` above `a`, which is in key order.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

`B` is U+0042 and `a` is U+0061, so `B` sorts first. Case-insensitive or locale collation would put `a` first, and §4.1.8 refuses collation.

The twin `parse/key-small-a-above-capital-b-refused` holds the same two keys the other way up and is refused.
