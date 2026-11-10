# Why this case exists

Two keys made only of digits, which §4.1.9 admits as `ident`: `9` above `10`, which is out of key order.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

§9.28: "`rows-out-of-order`: a table that declares a key, and a row whose key does not sort after the key of the row above it, as §4.1.8 orders text (§6)."

A key is an opaque identifier (§6), and code-point comparison does not change because a value looks like a number.

Nothing else in the file is refused, so `rows-out-of-order` is the only identifier §9 allows. The twin `parse/key-digits-10-above-9-accepted` is accepted.
