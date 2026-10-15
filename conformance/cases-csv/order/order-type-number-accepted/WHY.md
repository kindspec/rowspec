The sidecar declares `order_type` `number` over `o`, which holds `10` and
`-2.5`.

§13: "`order_type` declares the order column's type: one of the strings
`number`, `date` or `text`, and anything else, a non-string included, is
refused. Every trimmed value of the order column must then be of that type,
so a column of numbers declared `text` is refused even though it has a
single type."

Every value is a number, so the file is accepted.
