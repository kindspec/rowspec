`o` holds `1`, `apple` and `3`. A key is declared.

§13: "`order` names the column that orders the rows, and §6's order rules
apply to it. `key` is then required (§9.25). Each value of the column is
trimmed of ASCII space and tab only (§4.1.4), so a leading or trailing
non-ASCII space is part of it. A trimmed value is a `number` if it matches
§4.1.6's `number`, a `date` if it matches §4.1.7's `date`, and `text`
otherwise; no value matches both. So `1e3`, `+5` and `٥` are text, and
`2024-13-45` is a date, as in `.mdtbl`."

Two numbers and one text value: the column mixes types (§6: "Mixed types are
refused, because they have no total order").

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the mixed types is the only fault in the file and its sidecar,
so a reader that refuses it has refused for that reason or for one §13 does
not give. What the case does not pin is which reason the reader reports.

## Identifier

This case asserts `refusal: "bad-order-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "an `order` naming no column of the file, and an order column that mixes types, is blank in any row, or holds a non-finite value: §9.10 `bad-order-column`, whose "`c` is not a stored column" is the first."

§9.10: "`bad-order-column`: `order := by(c)` where `c` is not a stored column, is computed, mixes types, is blank in any row, or holds a non-finite spelling (`inf`, `nan`, `infinity`, any case, bare or after one leading `+` or `-`) in any row (§6)."

The column mixes types, and no `order_type` or `columns` is declared, so §9.27 cannot apply.

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `bad-order-column` instead.
