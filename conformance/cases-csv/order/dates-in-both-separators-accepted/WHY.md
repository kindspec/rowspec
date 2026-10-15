`o` holds `2024-01-05`, `2024/2/1` and `2023-12-31`. A key is declared.

§13: "`order` names the column that orders the rows, and §6's order rules
apply to it. `key` is then required (§9.25). Each value of the column is
trimmed of ASCII space and tab only (§4.1.4), so a leading or trailing
non-ASCII space is part of it. A trimmed value is a `number` if it matches
§4.1.6's `number`, a `date` if it matches §4.1.7's `date`, and `text`
otherwise; no value matches both. So `1e3`, `+5` and `٥` are text, and
`2024-13-45` is a date, as in `.mdtbl`."

Each value matches §4.1.7's `date`, whose two alternatives are the `-` and
`/` spellings and whose month and day may have one digit. §4.1.7: "Mixed
spellings in *different rows* of one column are all dates and do not make
the column mixed (§6)." The file is accepted.
