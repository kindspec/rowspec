# Why this case exists

The header is `id`, `a` padded with horizontal tabs, and `a`.

§13: "**A name is trimmed of ASCII space and tab only before §9.2 compares
it** … `a` with spaces or tabs around it and `a` are one name". So the
second and third names are one name, a duplicate (§9.2). No sidecar is
supplied and the field counts match, so §9.2 is the only refusal that can
apply.

## Identifier

This case asserts `refusal: "duplicate-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "two column names that compare alike, two empty header cells included: §9.2 `duplicate-column`."

§9.2: "`duplicate-column`: a duplicate column name"
