# Why this case exists

Two keys made only of digits, which §4.1.9 admits as `ident`: `10` above `9`, which is in key order.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

A key is an opaque identifier (§6), and code-point comparison does not change because a value looks like a number.

The twin `parse/key-digits-9-above-10-refused` holds the same two keys the other way up and is refused.
