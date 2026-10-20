The header holds `id` twice and a name with U+200B ZERO WIDTH SPACE, a `Cf` character, inside it.

## Identifier

This case asserts `refusal: ["bad-identifier", "duplicate-column"]`: each applies, and reporting any one passes.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a `Cf` format character in a column name, and a declared key's value that is empty or holds whitespace or a `Cf` format character: §9.16 `bad-identifier`."

§13: "two column names that compare alike, two empty header cells included: §9.2 `duplicate-column`."

§13: "A file can meet more than one of these, and then each applies, as §9 says: an order column of mixed types under an `order_type`, or under a `columns` type, meets both §9.10 and §9.27, because some of its values are not of the declared type."

§9.16: "`bad-identifier`: an identifier — column name, aggregate name, `key`/`order` argument, or a value of the key column — that is empty, or that contains whitespace, a `Cf` format character, or any character outside `ident` (§3, §4, §4.1.9)"

§9.2: "`duplicate-column`: a duplicate column name"

§9: "A conformance case that names one identifier is therefore a case in which exactly one refusal applies; where several apply, the case names each of them, and reporting any one passes."
