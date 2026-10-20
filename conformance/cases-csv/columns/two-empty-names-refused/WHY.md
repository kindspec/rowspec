# Why this case exists

Sibling of `repeated-empty-name-refused`, without the grouped-header shape:
an ordinary header `id,,` whose last two names are both the empty string.

§13: an empty header cell is a column name, and §9.2 refuses two names that
compare equal after NFC. Two empty names are a duplicate column.

This catches a fix that recognises only the grouped shape (one label
followed by a run of empty cells, real names on the next row) and refuses
that, while still letting the empty string through duplicate detection
everywhere else. The rule in §13 is about names, not about what the first
row looks like.

Exactly one refusal applies: no sidecar, so no key; three fields in each
row.

## Identifier

This case asserts `refusal: "duplicate-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "two column names that compare alike, two empty header cells included: §9.2 `duplicate-column`."

§9.2: "`duplicate-column`: a duplicate column name"
