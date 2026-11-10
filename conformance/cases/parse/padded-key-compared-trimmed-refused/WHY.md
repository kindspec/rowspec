# Why this case exists

The keys are `b` and `a`, with more padding before `b`.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

§4.1.4 trims a cell of leading and trailing `WSP`. Compared with the padding left on, the extra space before `b` sorts below `a` and the table would pass.

Nothing else in the file is refused, so `rows-out-of-order` is the only identifier §9 allows.
