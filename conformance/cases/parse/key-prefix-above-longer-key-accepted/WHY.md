# Why this case exists

One key a proper prefix of the other: `r_1` above `r_10`, which is in key order.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

Under code-point comparison of sequences the shorter sequence sorts first when it is a prefix of the longer.

The twin `parse/key-longer-key-above-prefix-refused` holds the same two keys the other way up and is refused.
