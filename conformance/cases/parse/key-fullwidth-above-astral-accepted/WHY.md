# Why this case exists

A key of U+FF21 and a key of U+1D400, both letters: `Ａ` above `𝐀`, which is in key order.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

The comparison is by code point, so U+FF21 sorts first. A comparison of UTF-16 code units would put U+1D400 first, because its high surrogate U+D835 is below U+FF21.

The twin `parse/key-astral-above-fullwidth-refused` holds the same two keys the other way up and is refused.
