# Why this case exists

An upper-case and a lower-case key: `a` above `B`, which is out of key order.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

§9.28: "`rows-out-of-order`: a table that declares a key, and a row whose key does not sort after the key of the row above it, as §4.1.8 orders text (§6)."

`B` is U+0042 and `a` is U+0061, so `B` sorts first. Case-insensitive or locale collation would put `a` first, and §4.1.8 refuses collation.

Nothing else in the file is refused, so `rows-out-of-order` is the only identifier §9 allows. The twin `parse/key-capital-b-above-small-a-accepted` is accepted.
