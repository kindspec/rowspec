The sidecar declares `order` with no `key`, and `o` holds `1` and `apple`.

## Identifier

This case asserts `refusal: ["bad-order-column", "order-without-key"]`: each applies, and reporting any one passes.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "`order` without `key`: §9.25 `order-without-key`."

§13: "an `order` naming no column of the file, and an order column that mixes types, is blank in any row, or holds a non-finite value: §9.10 `bad-order-column`, whose "`c` is not a stored column" is the first."

§13: "A file can meet more than one of these, and then each applies, as §9 says: an order column of mixed types under an `order_type`, or under a `columns` type, meets both §9.10 and §9.27, because some of its values are not of the declared type."

§9.10: "`bad-order-column`: `order := by(c)` where `c` is not a stored column, is computed, mixes types, is blank in any row, or holds a non-finite spelling (`inf`, `nan`, `infinity`, any case, bare or after one leading `+` or `-`) in any row (§6)."

§9.25: "`order-without-key`: `order := by(c)` in a table that declares no `key` (§6)."

§9: "A conformance case that names one identifier is therefore a case in which exactly one refusal applies; where several apply, the case names each of them, and reporting any one passes."

§13: "`order` names the column that orders the rows, and §6's order rules apply to it. `key` is then required (§9.25)."
