Two rows hold one order value, with keys `r_10` and `r_9`.

§13: "The rows MUST be in ascending order of the tuple `(typed value of the column, key)`, numbers by value, dates by year, month and day, text and the key as §4.1.8 orders text, or the file is refused (§9.28). A row may hold the same order value as the row above it, when its key sorts after that row's."

The key tiebreak compares by code point, so `r_10` sorts first.

The twin `order/tie-keys-r-9-above-r-10-refused` is refused.
