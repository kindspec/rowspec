`2024/1/5` and `2024-01-05` are one date (§4.1.7).

§13: "The rows MUST be in ascending order of the tuple `(typed value of the column, key)`, numbers by value, dates by year, month and day, text and the key as §4.1.8 orders text, or the file is refused (§9.28). A row may hold the same order value as the row above it, when its key sorts after that row's."

A tie on the date is broken by key.

The twin `order/date-tie-across-separators-keys-descend-refused` is refused.
