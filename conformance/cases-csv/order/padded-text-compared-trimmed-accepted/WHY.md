`o` holds `a` and `b`, the `b` with a leading space.

§13: "The rows MUST be in ascending order of the tuple `(typed value of the column, key)`, numbers by value, dates by year, month and day, text and the key as §4.1.8 orders text, or the file is refused (§9.28). A row may hold the same order value as the row above it, when its key sorts after that row's."

§13: "Each value of the column is trimmed of ASCII space and tab only". Compared with the space left on, the answer reverses.

The twin `order/padded-text-compared-trimmed-refused` is refused.
