`o` holds `1`, `<SP><TAB>2<TAB><SP>` and `3`. A key is declared.

§13: "`order` names the column that orders the rows, and §6's order rules
apply to it. `key` is then required (§9.25). Each value of the column is
trimmed of ASCII space and tab only (§4.1.4), so a leading or trailing
non-ASCII space is part of it. A trimmed value is a `number` if it matches
§4.1.6's `number`, a `date` if it matches §4.1.7's `date`, and `text`
otherwise; no value matches both. So `1e3`, `+5` and `٥` are text, and
`2024-13-45` is a date, as in `.mdtbl`."

Trimming removes the spaces and tabs, so the second value is `2` and the
column is three numbers. The control for
`order/no-break-space-padded-number-beside-numbers-refused`.
