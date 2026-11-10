# Why this case exists

A key of U+FF21 and a key of U+1D400, both letters: `𝐀` above `Ａ`, which is out of key order.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

§9.28: "`rows-out-of-order`: a table that declares a key, and a row whose key does not sort after the key of the row above it, as §4.1.8 orders text (§6)."

The comparison is by code point, so U+FF21 sorts first. A comparison of UTF-16 code units would put U+1D400 first, because its high surrogate U+D835 is below U+FF21.

Nothing else in the file is refused, so `rows-out-of-order` is the only identifier §9 allows. The twin `parse/key-fullwidth-above-astral-accepted` is accepted.
