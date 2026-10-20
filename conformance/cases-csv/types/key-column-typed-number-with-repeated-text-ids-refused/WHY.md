`columns` types the key column `id` as `number`; it holds `r1` twice.

## Identifier

This case asserts `refusal: ["column-type-mismatch", "duplicate-row-id"]`: each applies, and reporting any one passes.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a value of a column typed by `columns` that is not of that type, and an order column holding a value that is not of its `order_type`: §9.27 `column-type-mismatch`."

§13: "two rows with one value of the declared key: §9.5 `duplicate-row-id`."

§13: "A file can meet more than one of these, and then each applies, as §9 says: an order column of mixed types under an `order_type`, or under a `columns` type, meets both §9.10 and §9.27, because some of its values are not of the declared type."

§9.27: "`column-type-mismatch`: a stored value whose type is not the type declared for its column — in §13's CSV profile, by the sidecar's `columns` or its `order_type` (§13)."

§9.5: "`duplicate-row-id`: a duplicate row id, where a key is declared"

§9: "A conformance case that names one identifier is therefore a case in which exactly one refusal applies; where several apply, the case names each of them, and reporting any one passes."

§13: "Where it names the key or the order column, its check applies alongside theirs."
