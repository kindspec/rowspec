`r3`, with order value `3`, sits below the row with `5`: the shape of a file in which one line was moved without changing its order value.

§13: "The rows MUST be in ascending order of the tuple `(typed value of the column, key)`, numbers by value, dates by year, month and day, text and the key as §4.1.8 orders text, or the file is refused (§9.28). A row may hold the same order value as the row above it, when its key sorts after that row's."

The order value did not change, so the line does not belong where it now is, and the rule refuses it.

## Identifier

This case asserts `refusal: "rows-out-of-order"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "rows that do not follow the declared `order`, or the `key` where no `order` is declared: §9.28 `rows-out-of-order`."

§9.28: "`rows-out-of-order`: a table that declares a key, and a row whose key does not sort after the key of the row above it, as §4.1.8 orders text (§6). In §13's CSV profile, rows that do not follow the sidecar's `order`, or its `key` where it declares no `order` (§13)"
