`1.50` and `1.5` are one number.

§13: "The rows MUST be in ascending order of the tuple `(typed value of the column, key)`, numbers by value, dates by year, month and day, text and the key as §4.1.8 orders text, or the file is refused (§9.28). A row may hold the same order value as the row above it, when its key sorts after that row's."

A tie on the typed value is broken by key. Comparing the spellings as text would order these two the other way and ignore the key.

The twin `order/numeric-tie-after-typed-value-keys-descend-refused` is refused.
