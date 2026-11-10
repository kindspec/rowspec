# Why this case exists

Two keys ending in numbers: `r_9` above `r_10`, which is out of key order.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

§9.28: "`rows-out-of-order`: a table that declares a key, and a row whose key does not sort after the key of the row above it, as §4.1.8 orders text (§6)."

The comparison is by code point, and `1` (U+0031) precedes `9` (U+0039) at the third character. A numeric or natural sort would order them the other way.

Nothing else in the file is refused, so `rows-out-of-order` is the only identifier §9 allows. The twin `parse/key-r-10-above-r-9-accepted` is accepted.
