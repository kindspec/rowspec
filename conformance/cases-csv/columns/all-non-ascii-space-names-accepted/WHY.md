# Why this case exists

Every header name is a single non-ASCII space: U+00A0 NO-BREAK SPACE,
U+2003 EM SPACE and U+3000 IDEOGRAPHIC SPACE.

§13: column names "are exempt from §4.1.9's allowlist" — "Only a `Cf`
format character in a column name is still refused" — and "**A name is
trimmed of ASCII space and tab only before §9.2 compares it** … A leading or
trailing non-ASCII space, such as U+00A0, is part of the name". "names still
compare after NFC": NFC leaves all three characters as they are, so the
three names are distinct and the file is accepted.

A reader that trims Unicode whitespace sees three empty names, and one that
compares under NFKC sees three spaces; either refuses the file as a
duplicate.
