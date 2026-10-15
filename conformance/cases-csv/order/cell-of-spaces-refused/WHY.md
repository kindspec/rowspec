`o` holds `1`, a cell of three spaces, and `3`. A key is declared.

§13: "The column is refused (§6, §9.10) when it mixes types, **when it is
blank in any row**, a cell of spaces or tabs included, since blank is none
of the three types, and when it holds any non-finite spelling §9.10 lists,
in any row and whatever the rest of the column holds. A `number` whose
binary64 value is infinite, such as a four-hundred-digit one, is a
non-finite number, and is refused (§6). A file with no data rows has no
order values and is not refused on `order`."

Trimmed of ASCII space and tab, the second value is empty, so `o` is blank
in a row and is refused. The other two are numbers, so nothing else applies;
the column would otherwise sort.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the blank order value is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports.
