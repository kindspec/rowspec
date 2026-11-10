# Why this case exists

`key := k` names the second column. `k` ascends while the first column descends.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

The rule reads the declared key column, not the first column.
