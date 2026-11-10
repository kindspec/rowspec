# Why this case exists

Four rows, each key sorting after the one above.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

The plain accepted shape of the rule. `parse/rows-out-of-key-order-refused` is its refused twin.
