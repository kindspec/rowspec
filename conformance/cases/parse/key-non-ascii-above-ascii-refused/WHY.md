# Why this case exists

An ASCII key and a precomposed non-ASCII key: `é` above `z`, which is out of key order.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

§9.28: "`rows-out-of-order`: a table that declares a key, and a row whose key does not sort after the key of the row above it, as §4.1.8 orders text (§6)."

`z` is U+007A and `é` is U+00E9, so `z` sorts first. Locale collation would put `é` beside `e`, before `z`.

Nothing else in the file is refused, so `rows-out-of-order` is the only identifier §9 allows. The twin `parse/key-ascii-above-non-ascii-accepted` is accepted.
