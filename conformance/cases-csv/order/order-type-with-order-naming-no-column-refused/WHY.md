`order` names `p`, which is not a column, and `order_type` is `number`, a valid type.

## Identifier

This case asserts `refusal: "bad-order-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "an `order` naming no column of the file, and an order column that mixes types, is blank in any row, or holds a non-finite value: §9.10 `bad-order-column`, whose "`c` is not a stored column" is the first."

§13: "This list is complete: a sidecar is `malformed-declaration` for these reasons and no others, and the clause before the colon says why they are, without adding to them."

§13: "`order_type` is judged only against an order column that exists, so a valid `order_type` (one of `number`, `date` or `text`) beside an `order` naming no column is none of these, and that sidecar is §9.10 `bad-order-column` alone. A `columns` member naming that same missing column is still the last item."

§9.10: "`bad-order-column`: `order := by(c)` where `c` is not a stored column, is computed, mixes types, is blank in any row, or holds a non-finite spelling (`inf`, `nan`, `infinity`, any case, bare or after one leading `+` or `-`) in any row (§6)."

SPEC.md at `72f41cf` left open whether `order_type` beside a missing order column was also `malformed-declaration`; the amendment at `df99ea1` settles it: it is not.
