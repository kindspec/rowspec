`o` holds `1`, a `1` followed by 299 zeros (1e299), and `3`. A key is
declared.

§13: "The column is refused (§6, §9.10) when it mixes types, **when it is
blank in any row**, a cell of spaces or tabs included, since blank is none
of the three types, and when it holds any non-finite spelling §9.10 lists,
in any row and whatever the rest of the column holds. A `number` whose
binary64 value is infinite, such as a four-hundred-digit one, is a
non-finite number, and is refused (§6). A file with no data rows has no
order values and is not refused on `order`."

1e299 is below binary64's largest finite value, about 1.8e308, so the value
is a finite number and the column is three numbers. The control for
`order/four-hundred-digit-number-refused`: a reader that refuses on digit
count rather than on the binary64 value refuses this file.
