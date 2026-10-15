# Why this case exists

The file is one line: a single vertical tab (U+000B) followed by LF.

§13's record boundaries "are RFC 4180's", where a record ends at a line break,
and a line break there is CRLF or, as this profile reads it, LF. vertical tab is
neither, so the file is one record of one field: a header with one column,
named by that one character, and no data rows. A header-only file is a
zero-row table (`table/header-only-accepted`).

§13: "**column names are exempt from §4.1.9's allowlist.** ... Only a `Cf`
format character in a column name is still refused". U+000B is a control
character, general category `Cc`, not `Cf`.

§13: "**A name is trimmed of ASCII space and tab only before §9.2 compares
it**". vertical tab is not trimmed, so the name is not empty — and one name could
not be a duplicate anyway.

No refusal applies and the file is accepted. A reader that splits lines on
every character its host calls a line boundary — Python's `str.splitlines`
counts U+000B — sees two empty lines instead, and either finds no table or
refuses a second empty line.
