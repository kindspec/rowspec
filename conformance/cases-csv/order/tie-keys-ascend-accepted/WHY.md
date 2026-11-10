Two rows hold one order value.

§13: "The rows MUST be in ascending order of the tuple `(typed value of the column, key)`, numbers by value, dates by year, month and day, text and the key as §4.1.8 orders text, or the file is refused (§9.28). A row may hold the same order value as the row above it, when its key sorts after that row's."

§13 allows a tie "when its key sorts after that row's".

The twin `order/tie-keys-descend-refused` is refused.
