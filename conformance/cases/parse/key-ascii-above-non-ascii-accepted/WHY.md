# Why this case exists

An ASCII key and a precomposed non-ASCII key: `z` above `é`, which is in key order.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

`z` is U+007A and `é` is U+00E9, so `z` sorts first. Locale collation would put `é` beside `e`, before `z`.

The twin `parse/key-non-ascii-above-ascii-refused` holds the same two keys the other way up and is refused.
