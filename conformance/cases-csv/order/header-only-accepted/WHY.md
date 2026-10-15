The CSV is a header, `id,o`, and no data rows. The sidecar declares `key`
`id` and `order` `o`.

§13: "The column is refused (§6, §9.10) when it mixes types, **when it is
blank in any row**, a cell of spaces or tabs included, since blank is none
of the three types, and when it holds any non-finite spelling §9.10 lists,
in any row and whatever the rest of the column holds. A `number` whose
binary64 value is infinite, such as a four-hundred-digit one, is a
non-finite number, and is refused (§6). A file with no data rows has no
order values and is not refused on `order`."

"A file with no data rows has no order values and is not refused on
`order`." Both names name a column, so the file is accepted.
