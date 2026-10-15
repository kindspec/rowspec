`o` holds `apple`, a cell of one U+00A0 NO-BREAK SPACE, and `pear`. A key is
declared.

§13: "`order` names the column that orders the rows, and §6's order rules
apply to it. `key` is then required (§9.25). Each value of the column is
trimmed of ASCII space and tab only (§4.1.4), so a leading or trailing
non-ASCII space is part of it. A trimmed value is a `number` if it matches
§4.1.6's `number`, a `date` if it matches §4.1.7's `date`, and `text`
otherwise; no value matches both. So `1e3`, `+5` and `٥` are text, and
`2024-13-45` is a date, as in `.mdtbl`."

U+00A0 is not trimmed, so the second value is the one character U+00A0: not
blank, and `text`, as `apple` and `pear` are. The column has one type and no
blank, so the file is accepted. A reader that trims Unicode whitespace sees
a blank and refuses it.
