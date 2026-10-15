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
