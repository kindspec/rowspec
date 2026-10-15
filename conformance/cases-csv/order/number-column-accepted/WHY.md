The control for the `order/` group. The sidecar declares `key` `id` and
`order` `o`. `o` holds `10`, `-2.5` and `007`, every one a `number` under
§4.1.6.

§13: "`order` names the column that orders the rows, and §6's order rules
apply to it. `key` is then required (§9.25). Each value of the column is
trimmed of ASCII space and tab only (§4.1.4), so a leading or trailing
non-ASCII space is part of it. A trimmed value is a `number` if it matches
§4.1.6's `number`, a `date` if it matches §4.1.7's `date`, and `text`
otherwise; no value matches both. So `1e3`, `+5` and `٥` are text, and
`2024-13-45` is a date, as in `.mdtbl`."

The column has one type, no blank and no non-finite value, and a key is
declared, so the file is accepted.
