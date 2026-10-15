# Why this case exists

The header is `id`, a single U+00A0 NO-BREAK SPACE, and an empty cell.

§13: "**A name is trimmed of ASCII space and tab only before §9.2 compares
it**, as a key value is (§4.1.4): `a` with spaces or tabs around it and `a`
are one name, and so are a header cell of spaces, one of a tab and an empty
one, so any two of them are a duplicate. A leading or trailing non-ASCII
space, such as U+00A0, is part of the name, as it is part of a key value, so
`a` and `a<U+00A0>` are two names".

No sidecar is supplied, so no key is declared, and the data row has the
header's field count, so §9.2 is the only refusal that can apply.

U+00A0 is not trimmed, so the name U+00A0 and the empty name are two
names and the file is accepted.
