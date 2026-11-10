# Why this case exists

Two keys ending in numbers: `r_10` above `r_9`, which is in key order.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

The comparison is by code point, and `1` (U+0031) precedes `9` (U+0039) at the third character. A numeric or natural sort would order them the other way.

The twin `parse/key-r-9-above-r-10-refused` holds the same two keys the other way up and is refused.
