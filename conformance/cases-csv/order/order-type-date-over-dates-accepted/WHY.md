`order_type` is `date`, and `o` holds `2024-01-05` and `2024/2/1`.

§13: "`order_type` declares the order column's type: one of the strings
`number`, `date` or `text`, and anything else, a non-string included, is
refused. Every trimmed value of the order column must then be of that type,
so a column of numbers declared `text` is refused even though it has a
single type."

Both are dates, so the file is accepted.
