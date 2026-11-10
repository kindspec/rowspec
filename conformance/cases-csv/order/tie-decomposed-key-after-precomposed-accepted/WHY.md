Two rows hold one order value, with keys U+00E9 and U+0065 U+0301 U+0062.

§13: "The rows MUST be in ascending order of the tuple `(typed value of the column, key)`, numbers by value, dates by year, month and day, text and the key as §4.1.8 orders text, or the file is refused (§9.28). A row may hold the same order value as the row above it, when its key sorts after that row's."

The key tiebreak compares the NFC-normalised value, so `é` is a proper prefix of the longer key. Raw code points give the opposite answer.

The twin `order/tie-decomposed-key-above-precomposed-refused` is refused.
