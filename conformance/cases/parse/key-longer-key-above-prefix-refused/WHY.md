# Why this case exists

One key a proper prefix of the other: `r_10` above `r_1`, which is out of key order.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

§9.28: "`rows-out-of-order`: a table that declares a key, and a row whose key does not sort after the key of the row above it, as §4.1.8 orders text (§6)."

Under code-point comparison of sequences the shorter sequence sorts first when it is a prefix of the longer.

Nothing else in the file is refused, so `rows-out-of-order` is the only identifier §9 allows. The twin `parse/key-prefix-above-longer-key-accepted` is accepted.
