`o` is a number column, and the keys ascend in this case and its twin.

§13: "The rows MUST be in ascending order of the tuple `(typed value of the column, key)`, numbers by value, dates by year, month and day, text and the key as §4.1.8 orders text, or the file is refused (§9.28). A row may hold the same order value as the row above it, when its key sorts after that row's."

Numbers compare by value. `2` is below `10`, which text comparison would reverse.

The twin `order/rows-descend-by-number-refused` is refused.
