The one-byte twin of `order/order-type-number-accepted`: `-2.5` becomes `-2.5.`, which is `text`, so the column mixes types and holds a value that is not a `number`.

## Identifier

This case asserts `refusal: ["bad-order-column", "column-type-mismatch"]`: each applies, and reporting any one passes.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "A trimmed value is a `number` if it matches §4.1.6's `number`, a `date` if it matches §4.1.7's `date`, and `text` otherwise; no value matches both."

§13: "A file can meet more than one of these, and then each applies, as §9 says: an order column of mixed types under an `order_type`, or under a `columns` type, meets both §9.10 and §9.27, because some of its values are not of the declared type."

§9.10: "`bad-order-column`: `order := by(c)` where `c` is not a stored column, is computed, mixes types, is blank in any row, or holds a non-finite spelling (`inf`, `nan`, `infinity`, any case, bare or after one leading `+` or `-`) in any row (§6)."

§9.27: "`column-type-mismatch`: a stored value whose type is not the type declared for its column — in §13's CSV profile, by the sidecar's `columns` or its `order_type` (§13)."

§9: "A conformance case that names one identifier is therefore a case in which exactly one refusal applies; where several apply, the case names each of them, and reporting any one passes."
