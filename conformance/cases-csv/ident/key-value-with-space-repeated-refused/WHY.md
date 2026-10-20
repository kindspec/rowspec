The declared key holds `r 1` in both rows: a value with whitespace, and the same value twice.

## Identifier

This case asserts `refusal: ["bad-identifier", "duplicate-row-id"]`: each applies, and reporting any one passes.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a `Cf` format character in a column name, and a declared key's value that is empty or holds whitespace or a `Cf` format character: §9.16 `bad-identifier`."

§13: "two rows with one value of the declared key: §9.5 `duplicate-row-id`."

§13: "A file can meet more than one of these, and then each applies, as §9 says: an order column of mixed types under an `order_type`, or under a `columns` type, meets both §9.10 and §9.27, because some of its values are not of the declared type."

§9.16: "`bad-identifier`: an identifier — column name, aggregate name, `key`/`order` argument, or a value of the key column — that is empty, or that contains whitespace, a `Cf` format character, or any character outside `ident` (§3, §4, §4.1.9)"

§9.5: "`duplicate-row-id`: a duplicate row id, where a key is declared"

§9: "A conformance case that names one identifier is therefore a case in which exactly one refusal applies; where several apply, the case names each of them, and reporting any one passes."
