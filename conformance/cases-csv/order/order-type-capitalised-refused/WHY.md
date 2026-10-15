`order_type` is the string `Number`. `o` holds two numbers.

§13: "`order_type` declares the order column's type: one of the strings
`number`, `date` or `text`, and anything else, a non-string included, is
refused. Every trimmed value of the order column must then be of that type,
so a column of numbers declared `text` is refused even though it has a
single type."

The string `Number` is not one of the three strings, so the sidecar is
refused. Nothing in §13 folds case.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the `order_type` value is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports.
