`o` holds `1`, `٥` (U+0665 ARABIC-INDIC DIGIT FIVE), and `3`. A key is
declared.

§13: "`order` names the column that orders the rows, and §6's order rules
apply to it. `key` is then required (§9.25). Each value of the column is
trimmed of ASCII space and tab only (§4.1.4), so a leading or trailing
non-ASCII space is part of it. A trimmed value is a `number` if it matches
§4.1.6's `number`, a `date` if it matches §4.1.7's `date`, and `text`
otherwise; no value matches both. So `1e3`, `+5` and `٥` are text, and
`2024-13-45` is a date, as in `.mdtbl`."

`٥` (U+0665 ARABIC-INDIC DIGIT FIVE) is named there as text, so beside two
numbers the column mixes types and is refused. A reader that classifies with
its host's number parser reads three numbers and accepts.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the mixed types is the only fault in the file and its sidecar,
so a reader that refuses it has refused for that reason or for one §13 does
not give. What the case does not pin is which reason the reader reports.
