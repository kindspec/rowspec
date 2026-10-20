`o` holds `+nan`: `nan` after one leading `+`, in both rows. A key is
declared.

§13: "The column is refused (§6, §9.10) when it mixes types, **when it is
blank in any row**, a cell of spaces or tabs included, since blank is none
of the three types, and when it holds any non-finite spelling §9.10 lists,
in any row and whatever the rest of the column holds. A `number` whose
binary64 value is infinite, such as a four-hundred-digit one, is a
non-finite number, and is refused (§6). A file with no data rows has no
order values and is not refused on `order`."

§9.10 lists "a non-finite spelling (`inf`, `nan`, `infinity`, any case, bare
or after one leading `+` or `-`)".

§6: "Non-finite numbers in `c` are refused, and so is a non-finite
**spelling** (§9.10): `inf`, `nan` or `infinity` in any case, bare or after
one leading `+` or `-`." Read by type alone the column is one `text` column,
since a sign does not make the value a `number`; the spelling rule refuses
it.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the signed non-finite spelling is the only fault in the file
and its sidecar, so a reader that refuses it has refused for that reason or
for one §13 does not give. What the case does not pin is which reason the
reader reports.

## Identifier

This case asserts `refusal: "bad-order-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "an `order` naming no column of the file, and an order column that mixes types, is blank in any row, or holds a non-finite value: §9.10 `bad-order-column`, whose "`c` is not a stored column" is the first."

§9.10: "`bad-order-column`: `order := by(c)` where `c` is not a stored column, is computed, mixes types, is blank in any row, or holds a non-finite spelling (`inf`, `nan`, `infinity`, any case, bare or after one leading `+` or `-`) in any row (§6)."

The column holds a non-finite spelling.

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `bad-order-column` instead.
