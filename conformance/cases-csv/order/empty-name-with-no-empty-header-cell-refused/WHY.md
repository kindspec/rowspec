The sidecar's `order` is the empty string, and no header cell of the CSV
is empty (or blank): they are `id` and `v`. `key` names `id`.

§13: "A sidecar names a column as §9.2 compares names in this profile:
after trimming ASCII space and tab only, and after NFC. So `" joined"`
names the column `joined`, and `""` names a column whose header cell is
empty. A name that is not a string, or that names no column, is refused,
whichever member holds it: a declaration naming nothing is refused rather
than skipped, because skipping it switches off the check it asked for."

The empty name names no column, so it is refused. A reader that treats
an empty `order` as no order at all accepts this file.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the name naming no column is the only fault in the file and its sidecar, so a
reader that refuses it has refused for that reason or for one §13 does not
give. What the case does not pin is which reason the reader reports.

## Identifier

This case asserts `refusal: "bad-order-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "an `order` naming no column of the file, and an order column that mixes types, is blank in any row, or holds a non-finite value: §9.10 `bad-order-column`, whose "`c` is not a stored column" is the first."

§9.10: "`bad-order-column`: `order := by(c)` where `c` is not a stored column, is computed, mixes types, is blank in any row, or holds a non-finite spelling (`inf`, `nan`, `infinity`, any case, bare or after one leading `+` or `-`) in any row (§6)."

An `order` naming no column is §9.10, not §9.12: §13 sends only a `key` or a `columns` member naming no column to `malformed-declaration`.

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `bad-order-column` instead.
