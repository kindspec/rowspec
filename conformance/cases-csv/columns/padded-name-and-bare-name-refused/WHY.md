# Why this case exists

The header is `id`, `a`, and `a` with a space either side.

§13: "**A name is trimmed of ASCII space and tab only before §9.2 compares
it**, as a key value is (§4.1.4): `a` with spaces or tabs around it and `a`
are one name, and so are a header cell of spaces, one of a tab and an empty
one, so any two of them are a duplicate. A leading or trailing non-ASCII
space, such as U+00A0, is part of the name, as it is part of a key value, so
`a` and `a<U+00A0>` are two names".

No sidecar is supplied, so no key is declared, and the data row has the
header's field count, so §9.2 is the only refusal that can apply.

` a ` trims to `a`, so the two are a duplicate (§9.2).

## Identifier

This case asserts `refusal: "duplicate-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "two column names that compare alike, two empty header cells included: §9.2 `duplicate-column`."

§9.2: "`duplicate-column`: a duplicate column name"
