# Why this case exists

Eight rows, every adjacent pair in order except the last.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

§6 says "each data row", so the check reaches the final row and does not stop short of it.

Nothing else in the file is refused, so `rows-out-of-order` is the only identifier §9 allows.
