`o` holds U+00E9 and U+0065 U+0301 U+0062, whose NFC form is U+00E9 U+0062.

§13: "The rows MUST be in ascending order of the tuple `(typed value of the column, key)`, numbers by value, dates by year, month and day, text and the key as §4.1.8 orders text, or the file is refused (§9.28). A row may hold the same order value as the row above it, when its key sorts after that row's."

§4.1.8 compares the NFC-normalised value of a text order column, so `é` is a proper prefix of the longer value. Raw code points give the opposite answer.

The twin `order/text-column-decomposed-longer-above-precomposed-refused` is refused.
