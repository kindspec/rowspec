The sidecar declares `order` `o` and no `key`. `o` holds three numbers.

§13: "`order` names the column that orders the rows, and §6's order rules
apply to it. `key` is then required (§9.25). Each value of the column is
trimmed of ASCII space and tab only (§4.1.4), so a leading or trailing
non-ASCII space is part of it. A trimmed value is a `number` if it matches
§4.1.6's `number`, a `date` if it matches §4.1.7's `date`, and `text`
otherwise; no value matches both. So `1e3`, `+5` and `٥` are text, and
`2024-13-45` is a date, as in `.mdtbl`."

§9.25 (`order-without-key`) refuses "`order := by(c)` in a table that
declares no `key`". With a key this file is `order/number-column-accepted`.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the missing key is the only fault in the file and its sidecar,
so a reader that refuses it has refused for that reason or for one §13 does
not give. What the case does not pin is which reason the reader reports.
