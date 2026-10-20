`order_type` is `number` and `o` is blank in row `r2`. Read by §13's classification alone, a blank would be `text` and so not a `number`; §13 says a blank is not checked against `order_type`.

## Identifier

This case asserts `refusal: "bad-order-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "A trimmed value is a `number` if it matches §4.1.6's `number`, a `date` if it matches §4.1.7's `date`, and `text` otherwise; no value matches both."

§13: "A blank value is not checked against `order_type`, as it is not against `columns`: the blank rule above already refuses it."

§13: "an `order` naming no column of the file, and an order column that mixes types, is blank in any row, or holds a non-finite value: §9.10 `bad-order-column`, whose "`c` is not a stored column" is the first."

§9.10: "`bad-order-column`: `order := by(c)` where `c` is not a stored column, is computed, mixes types, is blank in any row, or holds a non-finite spelling (`inf`, `nan`, `infinity`, any case, bare or after one leading `+` or `-`) in any row (§6)."
