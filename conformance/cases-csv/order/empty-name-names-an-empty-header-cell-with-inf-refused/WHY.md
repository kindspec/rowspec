The header is `id` and an empty cell; the sidecar's `order` is the empty
string and `key` names `id`. The empty-headed column holds `b`, `a` and
`inf`.

§13: "A sidecar names a column as §9.2 compares names in this profile:
after trimming ASCII space and tab only, and after NFC. So `" joined"`
names the column `joined`, and `""` names a column whose header cell is
empty. A name that is not a string, or that names no column, is refused,
whichever member holds it: a declaration naming nothing is refused rather
than skipped, because skipping it switches off the check it asked for."

So the empty-headed column is the order column.

§13: "The column is refused (§6, §9.10) when it mixes types, when it is
blank in any row, a cell of spaces or tabs included, since blank is
none of the three types, and when it holds any non-finite spelling §9.10
lists, in any row and whatever the rest of the column holds."

§9.10 lists "a non-finite spelling (`inf`, `nan`, `infinity`, any case,
bare or after one leading `+` or `-`)".

All three values are text, so the column does not mix types, but `inf`
is a listed spelling, and the file is refused. A reader that treats an
empty `order` as no order at all checks no order column and accepts it.
`order/empty-name-names-an-empty-header-cell-accepted` is the same file
without the `inf` row.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the non-finite spelling is the only fault in the file and its sidecar, so a
reader that refuses it has refused for that reason or for one §13 does not
give. What the case does not pin is which reason the reader reports.
