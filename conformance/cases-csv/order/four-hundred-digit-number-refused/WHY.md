`o` holds `1`, a `1` followed by 399 zeros, and `3`. A key is declared.

§13: "The column is refused (§6, §9.10) when it mixes types, **when it is
blank in any row**, a cell of spaces or tabs included, since blank is none
of the three types, and when it holds any non-finite spelling §9.10 lists,
in any row and whatever the rest of the column holds. A `number` whose
binary64 value is infinite, such as a four-hundred-digit one, is a
non-finite number, and is refused (§6). A file with no data rows has no
order values and is not refused on `order`."

The second value matches `number`, so the column has one type, but its
binary64 value is infinite: it is "a four-hundred-digit one", and is
refused.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the non-finite number is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports.
