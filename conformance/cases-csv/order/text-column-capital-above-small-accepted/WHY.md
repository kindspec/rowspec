`o` is a text column.

§13: "The rows MUST be in ascending order of the tuple `(typed value of the column, key)`, numbers by value, dates by year, month and day, text and the key as §4.1.8 orders text, or the file is refused (§9.28). A row may hold the same order value as the row above it, when its key sorts after that row's."

Text compares by code point: `Z` is U+005A and `a` is U+0061. §4.1.8 refuses locale collation.

The twin `order/text-column-small-above-capital-refused` is refused.
