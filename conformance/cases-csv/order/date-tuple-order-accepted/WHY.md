`o` holds two dates, one written without zero padding.

§13: "The rows MUST be in ascending order of the tuple `(typed value of the column, key)`, numbers by value, dates by year, month and day, text and the key as §4.1.8 orders text, or the file is refused (§9.28). A row may hold the same order value as the row above it, when its key sorts after that row's."

§4.1.7: "Dates compare as the integer tuple `(y, m, d)`, never as strings." As strings `2026-2-1` would sort after `2026-03-01`.

The twin `order/date-tuple-order-refused` is refused.
